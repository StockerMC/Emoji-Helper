from discord.ext import commands
import discord
import asyncpg
import aiohttp
from utils.errors import *
from . import database
import traceback
import sys
from datetime import datetime
import re

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
			message = kwargs["message"]
			message = getattr(message, "id", message)
			reactions = kwargs.get("reactions")
			if reactions:
				return await self.bot.wait_for(event, check = lambda reaction, user:
				reaction.message.id == message
				and user == self.author
				and str(reaction.emoji) in reactions, timeout=timeout)
			else:
				return await self.bot.wait_for(event, check = lambda reaction, user:
				reaction.message.id == message
				and user == self.author, timeout=timeout)
		elif event == "raw_reaction_add":
			message = kwargs["message"].id
			reactions = kwargs.get("reactions")
			if reactions:
				return await self.bot.wait_for(event, check = lambda payload:
				payload.message_id == message
				and payload.user_id == self.author.id
				and str(payload.emoji) in reactions, timeout=timeout)
			else:
				return await self.bot.wait_for(event, check = lambda payload:
				payload.message_id == message
				and payload.user_id == self.author.id, timeout=timeout)

	def error(self, message):
		embed = discord.Embed(title=f"Error in command `{self.command}`", color=0xd63636, description=message)
		embed.set_footer(text=self.author, icon_url=self.author.avatar_url)
		return embed

class Bot(commands.Bot):
	def __init__(self, *args, **kwargs):
		self.config = kwargs.pop("config")
		super().__init__(*args, **kwargs)

	async def start(self, *args, **kwargs):
		self.session = aiohttp.ClientSession(loop=self.loop)
		self.prefixes = {}
		self.emojify_toggles = {}

		self.postgres_config = self.config["database"]
		del self.postgres_config["setup_completed"]
		self.pool = await asyncpg.create_pool(**self.postgres_config)
		
		self.bot_config = self.config["bot"]
		self.default_prefix = self.bot_config["default_prefix"]
		self.default_emojify_toggle = self.bot_config["default_emojify_toggle"]
		self.support_server = self.bot_config["support_server"]
		self.error_channel = self.bot_config["error_channel"]
		self.traceback_channel = self.bot_config["traceback_channel"]
		self.bug_channel = self.bot_config["bug_channel"]
		self.guild_log_channel = self.bot_config["guild_log_channel"]
		self.success_emoji = "\U00002705"
		self.error_emoji = "\U0000274c"

		self.bug_reports = {}
		self.color = 0xf9c94c

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

	async def format_perm(perm):
		return perm.replace('_', ' ').title()

	async def on_command_error(self, ctx, error): ## fix error handling
		error = getattr(error, "original", error)

		# if ctx.command.name == "add" and not isinstance(commands.CommandOnCooldown):
		# 	ctx.command.reset_cooldown(ctx)

		embed = discord.Embed(title=f"Error in command `{ctx.command}`", color=0xd63636)
		embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar_url)

		if isinstance(error, commands.MissingPermissions):
			embed.description = f"You do not have permission to do this.\nMissing permissions: {', '.join(self.format_perm(perm) for perm in error.missing_perms)}"

		elif isinstance(error, commands.NoPrivateMessage):
			embed.description = "This command can only be used in a guild."

		elif isinstance(error, commands.CheckFailure):
			embed.description = "This command is only usable by the bot owner."

		elif isinstance(error, commands.CommandOnCooldown):
			minutes, seconds = divmod(error.retry_after, 60)
			embed.description = f"This command is on cooldown for {ctx.command.name.rstrip('e')}ing emojis to prevent hitting the emoji adding rate limit. It is on cooldown for {f'{int(minutes)} minutes,' if minutes > 0 else ''} {int(seconds)} seconds"

		elif isinstance(error, EmojifyDisabled):
			embed.description = "This command is disabled in the guild."

		elif isinstance(error, BadZipFile):
			embed.description = "The file provided was not a zip file"

		elif isinstance(error, AssertionError):
			embed.description = "The URL provided was invalid."

		elif isinstance(error, URLNotImage):
			embed.description = "Could not get an image from the URL provided"

		elif isinstance(error, CantCompressImage):
			embed.description = "Could not compress this image. Please provide a smaller image when using the command again." # reword?

		elif isinstance(error, EmptyAttachmentName):
			embed.description = "The attachment provided did not have a name and no name was provided"
		
		elif isinstance(error, GuildEmojiAddRateLimited):
			embed.description = "The guild was rate limited by discord for adding emojis. There is no set time for when this will expire."

		# elif isinstance(error, NoEmojiSlots):
		# 	embed.description = "Maximum number of "

		elif match := re.match(r"Maximum number of(?P<animated> animated)? emojis reached \((?P<amount>\d+)\)", str(error)):
			animated = match.group("animated")
			amount = match.group("amount")
			embed.description = f"Maximum number of {'animated ' if animated else ''}emojis reached ({amount})"
		
		elif "validation regex" in str(error):
			embed.description = "The emoji name provided was invalid."

		elif "In image: File cannot be larger than 256.0 kb." in str(error) or isinstance(error, ResourceWarning): # replace with just 256.0 kb?
			embed.description = "The emoji image cannot be larger than 256 kb."

		else:
			error_channel = self.get_channel(self.error_channel)
			traceback_channel = self.get_channel(self.traceback_channel)

			if isinstance(error, discord.Forbidden):
				missing_perms = []
				me = ctx.guild.me
				if not me.guild_permissions.manage_emojis and ctx.command.name in ("add", "remove", "rename", "addmultiple", "removemultiple"):
					missing_perms.append("Manage Emojis")
				elif not me.permissions_in(ctx.channel).embed_links and ctx.command.name == "help":
					missing_perms.append("Embed Links")
					return await ctx.send(f"I do not have permissions to do this.\nMissing permissions: {', '.join(missing_perms)}")
				elif not me.permissions_in(ctx.channel).send_messages:
					return

				embed.description = f"I do not have permissions to do this.\nMissing permissions: {', '.join(missing_perms)}"

			lines = traceback.format_exception(type(error), error, error.__traceback__)

			paginator = commands.Paginator()
			[paginator.add_line(x) for x in ''.join(lines).split("\n")]
			
			await error_channel.send(f"{f'Exception in command `{ctx.command.name}`' if ctx.command else ''} by {ctx.author} \n{error}")
			
			for page in paginator.pages:
				await traceback_channel.send(page)

			embed.description = f"An unknown error happened:\n\n```{str(error)}```\n\nIf this error persists, please report it with the `{ctx.prefix}bug` command"
		
		embed.timestamp = datetime.utcnow()
		await ctx.send(embed=embed)

	async def on_error(self, event_method, *args, **kwargs):
		lines = traceback.format_exception(*sys.exc_info())
		paginator = commands.Paginator(prefix=f"<@{self.owner_id}>\n```")
		[paginator.add_line(x) for x in ''.joirn(lines).split("\n")]
		channel = self.get_channel(self.traceback_channel)
		for page in paginator:
			await channel.send(page)