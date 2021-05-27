import aiohttp
from .errors import URLNotImage, CantCompressImage, NoEmojiSlots
from .image import compress_image
import discord

def get_emoji_url(emoji_id, animated):
	return f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}?v=1"

async def fetch_emoji_image(url, bot):
	timeout = aiohttp.ClientTimeout(total=60)
	async with bot.session.get(url, timeout=timeout) as response:
		assert response.status == 200

		if not response.headers["content-type"].startswith("image"):
			raise URLNotImage
		image = await response.read()
		return image

async def parse_command_args(name, emojis):
	pass

async def read_attachment(attachment):
	image = {"image": await attachment.read(), "success": True}
	size = len(image) / 1000 # bytes / 1000 = kilobytes
	if size > 256:
		try:
			image = await compress_image(image)
		except CantCompressImage:
			image["success"] = False

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

async def add_emoji(guild, name, image, reason, format="all"):
	if not guild_has_emoji_slots(guild, format):
		raise NoEmojiSlots

	try:
		await guild.create_custom_emoji(name=name, image=image, reason=reason)
	except discord.HTTPException:
		raise NoEmojiSlots