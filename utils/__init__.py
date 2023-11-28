from __future__ import annotations

from .decorators import executor, reactiontimer
from .bot import Bot
from .context import Context
from .config import Config
from .emoji import EmojiCommand, get_emoji_url, emoji_can_be_added, find_emojis_in_iterable, string_is_url
from .image import compress_image
from .errors import *
from .converters import GuildEmojiConverter, PartialEmojiConverter, GuildConverter, EmojiNameConverter, EmojiTypeConverter
from .menu import EmojiListSource
from .zip import zip_emojis, unzip_file
from .logging import WebhookHandler
from .http import EmojiHTTPClient
from .cache import alru_cache
from .help import HelpCommand

# NOTE: should this be moved in cogs/emojis.py?

"""
https://github.com/Rapptz/discord.py/commit/d1a2ee46209917000e57612c0bdce29b5035e15a

The following function is used under the following license:

The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    import datetime

TimestampStyle = Literal['f', 'F', 'd', 'D', 't', 'T', 'R']

def format_dt(dt: datetime.datetime, /, style: Optional[TimestampStyle] = None) -> str:
    if style is None:
        return f'<t:{int(dt.timestamp())}>'
    return f'<t:{int(dt.timestamp())}:{style}>'
