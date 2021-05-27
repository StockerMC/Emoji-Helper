from discord.ext.commands import CommandError

# class EmojiHelperException(CommandError):
# 	"""The base class for all errors"""
# 	pass

class EmojifyDisabled(Exception):
	"""The emojify command is disabled"""
	pass

# class InvalidURL(Exception): # replaced with assertionerror
# 	"""The URL provided was invalid"""

class URLNotImage(Exception):
	"""The URL provided was not an image""" # or not a valid image?
	pass

class CantCompressImage(Exception):
	"""Unable to compress the image provided""" # (attempted resize size was below or equal to zero)
	pass

class NoEmojiSlots(Exception):
	"""The guild is out of emoji slots"""
	pass