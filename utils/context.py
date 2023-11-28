# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from __future__ import annotations

from discord.ext import commands
import discord
import re
from .converters import PartialEmojiConverter, EmojiNameConverter, GuildEmojiConverter
from .errors import CouldntConvertCommandArgs, WaitForTimeout, URLNotZip
from .emoji import string_is_url, PartialEmoji_
from .menu import EmojiListSource
from discord.ext import menus
import asyncio
import datetime
import inspect
from typing import (
    TYPE_CHECKING,
    overload,
    Literal,
    Optional,
    Union,
    Any
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from .bot import Bot
    import discord

    EmojiIterable = Union[list[discord.Emoji], tuple[discord.Emoji]]
    PartialEmojiIterable = Union[list[discord.PartialEmoji], tuple[discord.PartialEmoji]]

class CommandArguments:
    def __init__(self, args: dict[str, Any]):
        self.name: Optional[str] = args.get("name")
        self.url: Optional[str] = args.get("url")
        self.emoji: Optional[discord.Emoji] = args.get("emoji")
        self.emojis: Optional[list[discord.Emoji]] = args.get("emojis")
        self.partial_emojis: Optional[list[PartialEmoji_]] = args.get("partial_emojis")

class Context(commands.Context):
    # these typehints aren't 100% accurate (half are optional)
    # these are here because dpy isn't typed in 1.7.3
    if TYPE_CHECKING:
        bot: Bot
        message: discord.Message
        command: commands.Command
        author: Union[discord.Member, discord.User]
        guild: discord.Guild

    def default_check(self, *args) -> Literal[True]:
        return True

    @overload
    async def wait_for(self, event: Literal["message"], *, predicate: Callable[..., bool] = default_check, timeout: Optional[float] = None, **kwargs) -> discord.Message: ...

    @overload
    async def wait_for(self, event: Literal["raw_reaction_add"], *, predicate: Callable[..., bool] = default_check, timeout: Optional[float] = None, **kwargs) -> discord.RawReactionActionEvent: ...

    async def wait_for(self, event: str, *, predicate: Callable[..., bool] = default_check, timeout: Optional[float] = None, **kwargs):
        def check(arg) -> bool:
            if isinstance(arg, discord.Message):
                condition = (
                    arg.author == self.author and
                    arg.channel == self.channel
                )
            elif isinstance(arg, discord.RawReactionActionEvent):
                try:
                    emojis = kwargs["emojis"].values()
                except AttributeError:
                    emojis = kwargs["emojis"]

                condition = (
                    str(arg.emoji) in emojis and
                    arg.user_id == self.author.id and # type: ignore
                    arg.message_id == self.message.id
                )
            else:
                raise NotImplementedError(event)

            return predicate(arg) and condition

        return await self.bot.wait_for(event, check=check, timeout=timeout)

    @overload
    async def confirm(self, content: Optional[str] = None, *, embed: Optional[discord.Embed] = None, timeout: Optional[float] = None, return_message: Literal[True], **kwargs) -> tuple[bool, discord.Message]: ...

    @overload
    async def confirm(self, content: Optional[str] = None, *, embed: Optional[discord.Embed] = None, timeout: Optional[float] = None, return_message: Optional[Literal[False]] = None, **kwargs) -> bool: ...

    async def confirm(self, content: Optional[str] = None, *, embed: Optional[discord.Embed] = None, timeout: Optional[float] = None, return_message: Optional[bool] = None, **kwargs) -> Union[bool, tuple[bool, discord.Message]]:
        message = await self.send(content, embed=embed, **kwargs)
        success_emoji = self.bot.success_emoji
        error_emoji = self.bot.error_emoji
        await message.add_reaction(success_emoji)
        await message.add_reaction(error_emoji)
        payload = await self.wait_for("raw_reaction_add", message_id=message.id, emojis=[success_emoji, error_emoji], timeout=timeout)
        if str(payload.emoji) == success_emoji:
            if return_message is True:
                return True, message
            else:
                return True

        if return_message is True:
            return False, message
        else:
            return False

    async def error(self, message: str = ""):
        embed = self.command_error(message)
        await self.send(embed=embed)

    def get_emojis_named(self, *names) -> list[discord.Emoji]:
        lowered_names = [name.lower() for name in names]
        emojis = [emoji for emoji in self.guild.emojis if emoji.name.lower() in lowered_names]
        return emojis

    def get_emojis_by_type(self, emoji_type: str) -> list[discord.Emoji]:
        emoji_dict = { # can't think of a better name
            "all": list(self.guild.emojis),
            "animated": [emoji for emoji in self.guild.emojis if emoji.animated],
            "static": [emoji for emoji in self.guild.emojis if not emoji.animated]
        }

        return emoji_dict[emoji_type]

    @overload
    async def wait_for_emoji(self, emojis: EmojiIterable) -> discord.Emoji: ...

    @overload
    async def wait_for_emoji(self, emojis: PartialEmojiIterable) -> discord.PartialEmoji: ...

    async def wait_for_emoji(self, emojis: Union[EmojiIterable, PartialEmojiIterable]) -> Union[discord.Emoji, discord.PartialEmoji]:
        if len(emojis) == 1:
            return emojis[0]

        pages = menus.MenuPages(source=EmojiListSource(emojis, description=f"Multiple emojis were found with that name. Which one would you like to {self.command}?"), timeout=120, delete_message_after=True)
        await pages.start(self)
        try:
            message = await self.wait_for("message", timeout=120)
        except asyncio.TimeoutError:
            raise WaitForTimeout()
            
        content: str = message.content
        if not content.isdigit():
            raise commands.BadArgument("You did not provide a whole number.") # reword?

        try:
            emoji = emojis[int(content) - 1]
        except IndexError:
            raise commands.BadArgument("This emoji does not exist.") # reword?
        else:
            return emoji

    def command_error(self, message: str = "") -> discord.Embed:
        embed = discord.Embed(title=f"Error{f' in command `{self.command}`' if self.command is not None else ''}", description=message, color=0xD63636)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=self.author, icon_url=self.author.avatar_url) # type: ignore
        return embed

    # This was inspired by
    # https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/context.py#L166-L175
    async def tick(self, option: bool):
        success_emoji = self.bot.success_emoji
        error_emoji = self.bot.error_emoji
        arrow_emoji = self.bot.arrow_emoji
        emojis = {
            True: success_emoji,
            False: error_emoji,
            None: arrow_emoji
        }

        await self.message.add_reaction(emojis[option])

    async def untick(self, option: bool):
        success_emoji = self.bot.success_emoji
        error_emoji = self.bot.error_emoji
        arrow_emoji = self.bot.arrow_emoji
        emojis = {
            True: success_emoji,
            False: error_emoji,
            None: arrow_emoji
        }

        await self.message.remove_reaction(emojis[option], self.me)

    async def emojis_in_sting(self, string: str) -> list[str]:
        emoji_regex = r"(<a?:[a-zA-Z0-9_]{2,32}:[0-9]{18,22}>)"
        emoji_matches = [match for match in re.findall(emoji_regex, string)]
        return emoji_matches

    async def parse_add_command_args(self, args) -> Optional[dict]:
        if self.message.attachments:
            attachment: discord.Attachment = self.message.attachments[0]
            if args:
                name = args[0]
            else:
                try:
                    name = re.split(r"\W+", attachment.filename)[0]
                except IndexError:
                    raise commands.BadArgument("The file name of the attachment provided was invalid.") # reword?

            url = attachment.url
            return {
                "name": name,
                "url": url
            }

        if len(args) == 0: # change this?
            return None

        elif len(args) == 1:
            emoji = await PartialEmojiConverter().convert(self, args[0])
            name = emoji.name
            url = str(emoji.url)
            return {
                "name": name,
                "url": url
            }

        elif len(args) == 2:
            partial_emojis: list[discord.PartialEmoji] = []
            name: Optional[str] = None
            url: Optional[str] = None

            try:
                name = await EmojiNameConverter().convert(self, args[0])
            except commands.BadArgument as e: # if it wasn't a valid name, see if it's an emoji
                try:
                    partial_emojis.append(await commands.PartialEmojiConverter().convert(self, args[0]))
                except commands.PartialEmojiConversionFailure: # if it isn't an emoji, raise the original error about the name being invalid
                    raise e

            try:
                emoji = await commands.PartialEmojiConverter().convert(self, args[1])
            except commands.PartialEmojiConversionFailure:
                if not string_is_url(args[1]):
                    raise commands.BadArgument(f"Expected a custom emoji or URL, got {discord.utils.escape_markdown(args[1])}.")

                url = args[1].strip("<>")
            else:
                partial_emojis.append(emoji)

            return {
                "name": name,
                "url": url,
                "partial_emojis": partial_emojis
            }

        else:
            _partial_emojis: list[PartialEmoji_] = []
            for arg in args:
                try:
                    emoji = await commands.PartialEmojiConverter().convert(self, arg)
                    _partial_emojis.append(PartialEmoji_(emoji.name, emoji.animated, url=str(emoji.url)))
                except commands.PartialEmojiConversionFailure:
                    raise commands.BadArgument(f"Expected a custom emoji, got {discord.utils.escape_markdown(arg)} instead.")

            return {
                "partial_emojis": _partial_emojis
            }

    async def _parse_add_command_args(self, args) -> Optional[dict[str, Union[list[discord.PartialEmoji], str]]]:
        if len(args) == 0:
            return None

        content = " ".join(args)
        # get all the emojis from the content, regardless of whether they're separated by spaces or not
        emoji_matches = await self.emojis_in_sting(content)

        if emoji_matches:
            # remove the emojis from the content
            for match in emoji_matches:
                content = content.replace(match, "")

            if len(emoji_matches) > 1:
                # convert the matches to partial emojis
                partial_emojis: list[discord.PartialEmoji] = [await commands.PartialEmojiConverter().convert(self, emoji) for emoji in emoji_matches]
                return {
                    "partial_emojis": partial_emojis
                }
            else:
                partial_emoji: discord.PartialEmoji = await commands.PartialEmojiConverter().convert(self, emoji_matches[0])
                name = content.strip(" ")
                if name:
                    name = await EmojiNameConverter().convert(self, name)
                else:
                    name = partial_emoji.name
                return {
                    "name": name,
                    "url": str(partial_emoji.url)
                }
        else:
            items = content.split()
            name = items[0]
            url = None
            if len(items) > 1:
                url = items[1]

            name = await EmojiNameConverter().convert(self, name)
            if url is not None:
                if not string_is_url(url):
                    raise commands.BadArgument(f"Expected a custom emoji or URL, got {discord.utils.escape_markdown(url)}.")

            if url:
                return {
                    "name": name,
                    "url": url
                }
            else:
                return {
                    "name": name
                }

    async def parse_remove_command_args(self, args) -> Optional[dict[str, list[discord.Emoji]]]:
        if len(args) == 0:
            return None

        emojis = []
        for arg in args:
            try:
                emoji = await GuildEmojiConverter().convert(self, arg)
            except commands.EmojiNotFound:
                raise commands.BadArgument(f"Expected an emoji or emoji name from this guild, got {discord.utils.escape_markdown(arg)} instead.")
            else:
                emojis.append(emoji)

        return {
            "emojis": emojis
        }

    async def parse_rename_command_args(self, args) -> Optional[dict[str, Union[Union[discord.Emoji, discord.PartialEmoji], str]]]:
        if len(args) == 0:
            return None

        try:
            emoji = await GuildEmojiConverter().convert(self, args[0])
        except commands.EmojiNotFound:
            raise commands.BadArgument(f"Expected an emoji or emoji name from this guild, got {discord.utils.escape_markdown(args[0])} instead.")

        name = await EmojiNameConverter().convert(self, args[1])
        return {
            "emoji": emoji,
            "name": name
        }

    async def parse_import_command_args(self, args) -> dict[str, Any]:
        if args[0] is None and not self.message.attachments:
            raise commands.MissingRequiredArgument(inspect.Parameter("url", inspect.Parameter.POSITIONAL_OR_KEYWORD))

        url = args[0]
        if url is not None:
            zip_file_regex = r"(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*.zip)"
            if re.match(zip_file_regex, url) is None:
                raise URLNotZip
 
            return url
        else:
            url = self.message.attachments[0].proxy_url

        return {"url": url}

    async def parse_command_args(self) -> CommandArguments:
        parent: commands.Command = self.command.parent or self.command # type: ignore
        command_args: list[Any] = self.args[2:] # remove the self and ctx parameters
        parsers: dict[str, Callable] = {
            "add": self._parse_add_command_args, # remove the starting _ for add
            "remove": self.parse_remove_command_args,
            "rename": self.parse_rename_command_args,
            "import": self.parse_import_command_args
        }
        args: Optional[dict[str, Any]] = await parsers[parent.name](command_args)

        if args is None:
            raise CouldntConvertCommandArgs

        return CommandArguments(args)
