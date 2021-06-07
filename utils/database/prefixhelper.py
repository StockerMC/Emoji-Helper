import discord
from discord.ext import commands
from utils.bot import Bot

async def change_prefix(guild_id: int, prefix: str, bot: Bot):
	# if prefix == bot.default_prefix:
	# 	bot.prefixes[guild] = prefix
	# 	return
	
	await bot.pool.execute("""
		INSERT INTO prefixes
		VALUES ($1, $2)
		ON CONFLICT (guild)
		DO UPDATE
		SET prefix = $2
	""", guild_id, prefix)
	bot.prefixes[guild_id] = prefix

async def get_prefix(bot: Bot, message: discord.Message):
	if not message.guild:
		return commands.when_mentioned_or(bot.default_prefix)(bot, message)
	
	prefix = bot.prefixes.get(message.guild.id) # type: ignore
	if prefix:
		return commands.when_mentioned_or(prefix)(bot, message)
	
	prefix = await bot.pool.fetchval(
		"SELECT prefix FROM prefixes WHERE guild = $1",
		message.guild.id # type: ignore
	)
	prefix = prefix or bot.default_prefix

	bot.prefixes[message.guild.id] = prefix # type: ignore
	return commands.when_mentioned_or(prefix)(bot, message)

async def get_guild_prefix(guild_id: int, bot: Bot): # no need to fetch from database since prefixes are cached in get_prefix
	prefix = bot.prefixes.get(guild_id)
	return prefix

async def delete_prefix(guild_id: int, bot: Bot):
	await bot.pool.execute("""DELETE FROM prefixes WHERE guild = $1""", guild_id)
	try:
		del bot.prefixes[guild_id]
	except KeyError:
		pass