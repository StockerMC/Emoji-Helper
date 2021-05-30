from discord.ext import commands

async def change_emojify(guild, emojify, bot):
	# if emojify == bot.default_emojify_toggle:
	# 	bot.prefixes[guild] = emojify
	# 	return
	
	await bot.pool.execute("""
		INSERT INTO emojify_toggles
		VALUES ($1, $2)
		ON CONFLICT (guild)
		DO UPDATE
		SET emojify = $2
	""", guild, emojify)
	
	bot.emojify_toggles[guild] = emojify

async def get_emojify(guild, bot):	
	emojify = bot.emojify_toggles.get(guild)
	if emojify:
		return emojify
	
	emojify = await bot.pool.fetchval(
		"SELECT emojify FROM emojify_toggles WHERE guild = $1",
		guild
	)

	emojify = emojify or bot.default_emojify_toggle

	bot.emojify_toggles[guild] = emojify
	return emojify

async def toggle_emojify(guild, bot):
	emojify = await get_emojify(guild, bot)
	await change_emojify(guild, not emojify, bot)

async def delete_emojify(guild, bot):
	await bot.pool.execute("""DELETE FROM emojify_toggles WHERE guild = $1""", guild)
	try:
		del bot.emojify_toggles[guild]
	except KeyError:
		pass