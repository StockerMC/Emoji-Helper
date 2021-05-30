from discord.ext.commands import CommandError
from zipfile import BadZipFile

class EmojifyDisabled(Exception):
	"""The emojify command is disabled"""
	pass

class URLNotImage(Exception):
	"""The URL provided was not an image""" # or not a valid image?
	pass

class CantCompressImage(Exception):
	"""Unable to compress the image provided""" # (attempted resize size was below or equal to zero)
	pass

class NoEmojiSlots(Exception):
	"""The guild is out of emoji slots"""
	pass

class EmptyAttachmentName(Exception):
	"""The attachment did not have a name and no name was provided"""
	pass

class NoCustomEmoji(Exception):
	"""No custom emojis were provided"""
	pass

class GuildEmojiAddRateLimited(Exception):
	"""The guild is rate limited for adding emojis without being on cooldown"""