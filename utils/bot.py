from discord.ext import commands
import discord
import asyncpg
import aiohttp
from utils.errors import *
from . import database
import traceback

class Help(commands.MinimalHelpCommand): ## make better help command
	async def send_pages(self):
		destination = self.get_destination()
		for page in self.paginator.pages:
			embed = discord.Embed(description=page)
			await destination.send(embed=embed)

class Context(commands.Context):
	async def wait_for(self, event, timeout=None, **kwargs):
		if event == "message":
			if kwargs.get("numeric"):
				return await self.bot.wait_for(event, check = lambda message:
				message.author == self.author
				and message.channel == self.channel
				and message.content.isnumeric(), timeout=timeout)
			else:
				return await self.bot.wait_for(event, check = lambda message:
				message.author == self.author
				and message.channel == self.channel, timeout=timeout)
		elif event == "reaction_add":
			reactions = kwargs.get("reactions")
			if reactions:
				return await self.bot.wait_for(event, check = lambda reaction, user:
				reaction.message == kwargs.get("message")
				and user == self.author
				and str(reaction.emoji) in reactions, timeout=timeout)
			else:
				return await self.bot.wait_for(event, check = lambda reaction, user:
				reaction.message == kwargs.get("message")
				and user == self.author
				and str(reaction.emoji), timeout=timeout)

class Bot(commands.Bot):
	def __init__(self, *args, **kwargs):
		self.config = kwargs.pop("config")
		super().__init__(*args, **kwargs)

	async def start(self, *args, **kwargs):
		self.postgres_config = self.config["database"]
		del self.postgres_config["setup_completed"]
		self.pool = await asyncpg.create_pool(**self.postgres_config)
		self.prefixes = {}
		self.emojify_toggles = {}
		self.session = aiohttp.ClientSession(loop=self.loop)
		self.default_prefix = "e!"
		self.default_emojify_toggle = True
		self.support_server = "https://discord.gg/nptFDCVPWX"
		self.error_channel = 825852962784935956
		self.traceback_channel = 847980078813282315
		self.bug_channel = 837717191871823892
		self.guild_log_channel = 828809272573820999
		self.success_emoji = "<:success:835736813929758740>"
		self.error_emoji = "<:error:836034660932386816>"

		return await super().start(*args, **kwargs)

	async def get_context(self, message, *, cls=Context):
		return await super().get_context(message, cls=cls)

	async def on_message(self, message):
		if message.author.bot:
			return
		ctx = await self.get_context(message, cls=Context)
		await self.invoke(ctx)

	async def close(self):
		await self.session.close()
		await self.pool.close()
		return await super().close()

	async def on_ready(self):
		# print("fix import export #bugs")
		print(f"{self.user.name} is now ONLINE!")

	async def on_guild_join(self, guild):
		channel = self.get_channel(self.guild_log_channel)
		await channel.send(f"The bot has been added to `{guild}`. The bot is now in `{len(self.guilds)}` servers")

	async def on_guild_remove(self, guild):
		await database.delete_prefix(guild.id, self)
		await database.delete_emojify(guild.id, self)
		channel = self.get_channel(self.guild_log_channel)
		await channel.send(f"The bot has been removed from `{guild}`. The bot is now in `{len(self.guilds)}` servers")

	async def on_command_error(self, ctx, error): ## fix error handling
		# if isinstance(error, PartialEmojiConversionFailure):
		# 	return await ctx.send("Expected a custom emoji, got something else.")
		if isinstance(error, commands.MissingPermissions):
			return await ctx.send(f"<:error:836034660932386816> You do not have permissions to do this.\nMissing permissions: {', '.join(error.missing_perms)}")

		elif isinstance(error, commands.NoPrivateMessage):
			return await ctx.send("This command can only be used in a guild.")

		elif isinstance(error, commands.CheckFailure):
			return await ctx.send("You do not own this bot.")

		elif isinstance(error, commands.CommandOnCooldown):
			return await ctx.send(f"This command is on cooldown for {round(error.retry_after, 2)} seconds")

		else: ## rewrite error handling
			error_channel = self.get_channel(self.error_channel)
			traceback_channel = self.get_channel(self.traceback_channel)

			error_ = getattr(error, "original", error)
			if isinstance(error_, discord.Forbidden):
				missing_perms = []
				me = ctx.guild.me
				if not me.guild_permissions.manage_emojis and ctx.command.name in ("add", "remove", "rename", "addmultiple", "removemultiple"):
					missing_perms.append("manage_emojis")
				elif not me.permissions_in(ctx.channel).embed_links and ctx.command.name == "help":
					missing_perms.append("embed_links")
				
				return await ctx.send(f"<:error:836034660932386816> I do not have permissions to do this.\nMissing permissions: {', '.join(missing_perms)}")

			if isinstance(error_, EmojifyDisabled):
				return await ctx.send("<:error:836034660932386816> This command is disabled in the guild.")

			if "ResourceWarning" in str(error):
				return await ctx.send("Command raised an exception: HTTPException: 400 Bad Request (error code: 50035): Invalid Form Body\nIn image: File cannot be larger than 256.0 kb.")

			await ctx.send(str(error), allowed_mentions=discord.AllowedMentions.none())
			# if not isinstance(error, commands.CommandNotFound):
			# 	raise error

			error_type = type(error)
			error_trace = error.__traceback__

			# 'traceback' is the stdlib module, `import traceback`.
			lines = traceback.format_exception(error_type, error, error_trace)

			# format_exception returns a list with line breaks embedded in the lines, so let's just stitch the elements together
			paginator = commands.Paginator()
			[paginator.add_line(x) for x in ''.join(lines).split("\n")]
			
			await error_channel.send(f"{f'Exception in command {ctx.command.name}' if ctx.command else ''} by {ctx.author} \n{error}")
			
			for page in paginator.pages:
				await traceback_channel.send(page)