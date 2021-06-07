from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from utils.bot import Bot

async def change_emojify(guild_id: int, emojify: bool, bot: Bot):
	# if emojify == bot.default_emojify_toggle:
	# 	bot.prefixes[guild] = emojify
	# 	return
	
	await bot.pool.execute("""
		INSERT INTO emojify_toggles
		VALUES ($1, $2)
		ON CONFLICT (guild)
		DO UPDATE
		SET emojify = $2
	""", guild_id, emojify)
	
	bot.emojify_toggles[guild_id] = emojify

async def get_emojify(guild_id: int, bot: Bot):	
	emojify = bot.emojify_toggles.get(guild_id)
	if emojify:
		return emojify
	
	emojify = await bot.pool.fetchval(
		"SELECT emojify FROM emojify_toggles WHERE guild = $1",
		guild_id
	)

	emojify = emojify or bot.default_emojify_toggle

	bot.emojify_toggles[guild_id] = emojify
	return emojify

async def toggle_emojify(guild_id: int, bot: Bot):
	emojify = await get_emojify(guild_id, bot)
	await change_emojify(guild_id, not emojify, bot)

async def delete_emojify(guild_id: int, bot: Bot):
	await bot.pool.execute("""DELETE FROM emojify_toggles WHERE guild = $1""", guild_id)
	try:
		del bot.emojify_toggles[guild_id]
	except KeyError:
		pass