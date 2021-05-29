from discord.ext.commands import CommandError

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