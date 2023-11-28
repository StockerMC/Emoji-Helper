# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from typing import Union

class WaitForTimeout(Exception):
    """When a wait_for has it's timeout reached"""
    def __init__(self):
        super().__init__("This message has expired.") # reword?

class EmojifyDisabled(Exception):
    """The emojify command is disabled"""
    pass

class RateLimited(Exception):
    """The guild is being rate limited for the emojis endpoint"""
    def __init__(self, retry_after: float):
        self.retry_after = retry_after

class URLNotImage(Exception):
    """The URL provided was not an image""" # or not a valid image?
    pass

class URLNotZip(Exception):
    """The URL provided was not a zip file""" # or not a valid image?
    pass

class CantCompressImage(Exception):
    """Unable to compress the image provided""" # (attempted resize width or height was below 32 pixels)
    pass

class CantConvertImage(Exception):
    """Unable to convert the image provided"""
    pass

class NoEmojiSlots(Exception):
    """The guild is out of emoji slots"""
    
    def __init__(self, animated: Union[bool, None], max: int):
        if animated:
            self.type = "animated"
        elif not animated:
            self.type = "static"
        else: # if it's None
            self.type = ""

        self.max = max

class EmptyAttachmentName(Exception):
    """The attachment did not have a name and no name was provided"""
    pass

class NoCustomEmoji(Exception):
    """No custom emojis were provided"""
    pass

class GuildEmojiAddRateLimited(Exception):
    """The guild is rate limited for adding emojis"""
    pass

class CouldntConvertCommandArgs(Exception):
    """Failed to convert the command arguments""" # more descriptive?
    pass
