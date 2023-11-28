# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from __future__ import annotations

from .image import compress_image
from .decorators import reactiontimer
import re
from .errors import NoEmojiSlots
from discord.ext import commands
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union, Optional

if TYPE_CHECKING:
    from collections.abc import Iterable
    from discord import Guild

# class EmbedCommand(commands.Command):
#     """Command class that makes sure that the bot has permissions to send embeds"""

#     def __init__(self, func, **kwargs):
#         super().__init__(func, **kwargs)
#         self.add_check(commands.has_permissions(embed_links=True).predicate)

class EmojiCommand(commands.Command):
    """Command class that makes sure that the author and user have manage emoji permissions
    and that it was in a guild. This also decorates the command with decorators.reactiontimer
    """

    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        self = reactiontimer(self) # we could override __call__ but this is easier
        self.add_check(commands.has_permissions(manage_emojis=True).predicate)
        self.add_check(commands.bot_has_permissions(manage_emojis=True).predicate)
        self.add_check(commands.guild_only().predicate)

@dataclass
class PartialEmoji_:
    name: str
    animated: bool
    url: Optional[str] = None
    image: Optional[bytes] = None

def get_emoji_url(emoji_id: Union[str, int], animated: bool) -> str:
    return f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}?v=1"

def guild_has_emoji_slots(guild: Guild, format: str):
    emoji_limit = guild.emoji_limit
    if format == "animated":
        animated = True
    elif format == "static":
        animated = False
    else:
        animated = None

    static_emojis = len([emoji for emoji in guild.emojis if not emoji.animated])
    animated_emojis = len([emoji for emoji in guild.emojis if emoji.animated])
    
    if (
        (not animated and static_emojis >= emoji_limit) or
        (animated and animated_emojis >= emoji_limit) or
        (animated is None and animated_emojis >= emoji_limit and static_emojis >= emoji_limit)
    ):
        raise NoEmojiSlots(animated, emoji_limit)

def emoji_can_be_added(guild: Guild, animated: bool) -> bool:
    emoji_limit = guild.emoji_limit
    static_emojis = len([emoji for emoji in guild.emojis if not emoji.animated])
    animated_emojis = len([emoji for emoji in guild.emojis if emoji.animated])

    if animated:
        if animated_emojis >= emoji_limit:
            return False
    else:
        if static_emojis >= emoji_limit:
            return False

    return True

def find_emojis_in_iterable(iterable: Iterable) -> list[str]:
    string = "".join(iterable)
    emoji_regex = r"<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>"
    return re.findall(emoji_regex, string)

def string_is_url(string: str) -> bool:
    url_regex = r"<?(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*)>?"
    return re.match(url_regex, string) is not None
