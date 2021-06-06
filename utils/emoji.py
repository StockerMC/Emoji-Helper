import aiohttp
from .errors import URLNotImage, GuildEmojiAddRateLimited, NoEmojiSlots
from .image import compress_image
import discord
import asyncio
from .bot import Bot
from discord.utils import _bytes_to_base64_data

def get_emoji_url(emoji_id, animated):
	return f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}?v=1"

async def fetch_emoji_image(url, bot):
	timeout = aiohttp.ClientTimeout(total=60) # type: ignore
	async with bot.session.get(url, timeout=timeout) as response:
		assert response.status == 200

		if not response.headers["content-type"].startswith("image"):
			raise URLNotImage
		image = await response.read()
		return image

async def parse_command_args(name, emojis):
	pass

async def read_attachment(attachment, bot):
	image = await attachment.read()
	size = len(image) / 1000 # bytes / 1000 = kilobytes
	if size > 256:
		image = await bot.loop.run_in_executor(None, compress_image, image)

	return image

def guild_has_emoji_slots(guild, format):
	emoji_limit = guild.emoji_limit
	static_emojis = len([emoji for emoji in guild.emojis if not emoji.animated])
	animated_emojis = len([emoji for emoji in guild.emojis if emoji.animated])
	
	if format == "static" and static_emojis >= emoji_limit:
		return False

	elif format == "animated" and animated_emojis >= emoji_limit:
		return False

	elif format == "all" and animated_emojis >= emoji_limit and static_emojis >= emoji_limit:
		return False

	return True

async def add_emoji(guild, name, image, reason, format="static"):
	if not guild_has_emoji_slots(guild, format):
		raise NoEmojiSlots

	try:
		await guild.create_custom_emoji(name=name, image=image, reason=reason)
	except discord.HTTPException:
		raise NoEmojiSlots

from typing import Coroutine

async def safe_add_emoji(create_emoji_coro): # sees if guild is rate limited
	task = asyncio.create_task(create_emoji_coro)
	task2 = asyncio.create_task(asyncio.sleep(6))
	done, pending = await asyncio.wait({
		task,
		task2
	}, return_when=asyncio.FIRST_COMPLETED)
	
	result = done.pop().result()
	if not result: # if the sleep returned first
		raise GuildEmojiAddRateLimited

	for future in pending:
		future.cancel()

	return result

# async def add_emoji_api_request(bot, guild, image, name, reason):
# 	# async with bot.__session
# 	payload = {
# 		"name": name,
# 		"image": _bytes_to_base64_data(image),
# 		"roles": []
# 	}