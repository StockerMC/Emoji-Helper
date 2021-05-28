from discord.ext import commands
import discord
import asyncpg
import aiohttp
from utils.errors import *
from . import database

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
		self.error_channel = 824757004085755934
		self.bug_channel = 837717191871823892
		self.guild_log_channel = 824757004085755934
		self.success_emoji = "<:success:835736813929758740>"
		self.error_emoji = "<:error:836034660932386816>"

		prefixes = {
			"821733978381352991": "e!",
			"832662774647750716": "e!",
			"819502013095477249": "e!",
			"828292016902242354": "e!",
			"831861051078344704": "e!",
			"830569934848524298": "e!",
			"813518878884757534": "e!",
			"822296124492480524": "e!",
			"769241305401262081": "e!",
			"801489936373121064": "e!",
			"828153667940122634": "e!",
			"786643908125261854": "e!",
			"807089766523731988": "e!",
			"822503722684776559": "e!",
			"830572070047449128": "e!",
			"824661850230358057": "e!",
			"783782621855219732": "e!",
			"820851381769469974": "e!",
			"826160813140213760": "e!",
			"722558166289875065": "e!",
			"827341929992814622": "e!",
			"814870197230895134": "e!",
			"808405619345719337": "e!",
			"785029338231865386": "e!",
			"833495743721242687": "e!",
			"824809437025927198": "e!",
			"811697970851348480": "e!",
			"763048082899861515": "e!",
			"828340401688674375": "e!",
			"821603056163618818": "e!",
			"819317774542962735": "e!",
			"822485147323596811": "e!",
			"834210887295696966": "e!",
			"340565575707262997": "e!",
			"707243115869765643": "e!",
			"826709482439835649": "e!",
			"798318821336809472": "e!",
			"830157412341252106": "e!",
			"830660116319698945": "e!",
			"811258432816021514": "e!",
			"828733430133030944": "e!",
			"828779350596780032": "!",
			"823918014252056586": "e!",
			"828828096534675476": "e!",
			"828334744978063390": "e!",
			"822700924162146325": "e!",
			"830915666453332039": "ee",
			"766664483049308211": "e!",
			"801609699995942912": "e!",
			"816078245433966672": "e!",
			"830763793620926496": "e!",
			"809853299058671669": "e!",
			"826506392940445768": "e!",
			"826940549394858054": "e!",
			"832937830304055317": "e!",
			"831215296940605480": "e!",
			"833583375109324862": "/",
			"758808796708601857": "e!",
			"667238836086243339": "e!",
			"825599184680779786": "e!",
			"824757004085755934": "e!",
			"834012175491399711": "/",
			"830229655020634172": "e!",
			"826178778156892180": "e!",
			"820526256150937641": "e!",
			"824532190422892604": "e!",
			"829188215188881439": "!",
			"817671654128746497": "e!",
			"491085007033729024": "e!",
			"747247058468995133": "emoji",
			"827274565142839306": "e!",
			"828620467026919488": "e!",
			"827947457269989436": "e!",
			"826821200646242355": "e!",
			"800512888124604436": "e!",
			"816069256856731678": "e!",
			"830513046392668190": "e!",
			"833968018379767819": "e!",
			"834210580000145409": "e!",
			"825414337681162240": "++",
			"824858152125202442": "e!",
			"780545062948831282": "e!",
			"831542743779901450": "e!",
			"832024366664384512": "&",
			"832016829828038737": "e!",
			"821839587760406558": "e!",
			"817133834508304435": "e!",
			"832469696213155881": "e!",
			"827420758912663562": "e!",
			"804369905025024071": "e!",
			"831476156871606302": "e!",
			"818809814637346847": "e!",
			"763459638565011488": "e!",
			"710710854118801408": "e!",
			"365525995761041410": "e!",
			"828379414143303741": "e!",
			"833433244087222342": "e!"
		}

		prefixes = {k: v for k, v in prefixes if v != "e!"}
		for guild, prefix in prefixes.items():
			from .database import change_prefix
			await change_prefix(int(guild), prefix, self)

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
			if not isinstance(error, commands.CommandNotFound):
				raise error
			
			await error_channel.send(f"{error}\n{ctx.author}")