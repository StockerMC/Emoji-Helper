from discord.ext import commands

async def change_prefix(guild, prefix, bot):
	if prefix == bot.default_prefix:
		bot.prefixes[guild] = prefix
		return
	
	await bot.pool.execute("""
		INSERT INTO prefixes
		VALUES ($1, $2)
		ON CONFLICT (guild)
		DO UPDATE
		SET prefix = $2
	""", guild, prefix)
	bot.prefixes[guild] = prefix

async def get_prefix(bot, message):
	if not message.guild:
		return commands.when_mentioned_or(bot.default_prefixes)(bot, message)
	
	prefix = bot.prefixes.get(message.guild.id)
	if prefix:
		return commands.when_mentioned_or(prefix)(bot, message)
	
	prefix = await bot.pool.fetchval(
		"SELECT prefix FROM prefixes WHERE guild = $1",
		message.guild.id
	)
	prefix = prefix or bot.default_prefix

	bot.prefixes[message.guild.id] = prefix
	return commands.when_mentioned_or(prefix)(bot, message)

async def get_guild_prefix(guild, bot): # fetching from database might be completely useless since prefixes are cached in get_prefix
	prefix = bot.prefixes.get(guild)
	if prefix is not None:
		import json
		json.dump
		return prefix

	prefix = await bot.pool.fetchval(
		"SELECT prefix FROM prefixes WHERE guild = $1",
		guild
	)
	bot.prefixes[guild] = prefix
	return prefix

async def delete_prefix(guild, bot):
	await bot.pool.execute("""DELETE FROM prefixes WHERE guild = $1""", guild)
	try:
		del bot.prefixes[guild]
	except KeyError:
		pass