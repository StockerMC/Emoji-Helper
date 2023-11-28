# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from __future__ import annotations

from discord.ext import commands
import discord
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context

class GuildEmojiConverter(commands.EmojiConverter):
    async def convert(self, ctx: Context, argument: str) -> discord.Emoji:
        try:
            emoji = await super().convert(ctx, argument)
        except commands.EmojiNotFound:
            emojis = ctx.get_emojis_named(argument)
            if not emojis:
                raise commands.EmojiNotFound(argument)

            emoji = await ctx.wait_for_emoji(emojis)
        else:
            if emoji not in ctx.guild.emojis:
                raise commands.EmojiNotFound(argument)

        return emoji

class PartialEmojiConverter(commands.PartialEmojiConverter):
    async def convert(self, ctx: Context, argument: str) -> discord.PartialEmoji:
        emoji = await super().convert(ctx, argument)
        if emoji.id not in [emoji.id for emoji in ctx.guild.emojis]:
            raise commands.EmojiNotFound(argument)

        return emoji

class GuildConverter(commands.GuildConverter):
    async def convert(self, ctx: Context, argument: str) -> discord.Guild:
        try:
            guild = await super().convert(ctx, argument)
        except commands.GuildNotFound:
            def predicate(guild: discord.Guild):
                return guild.name.lower() == argument.lower()

            guild = discord.utils.find(predicate, ctx.bot.guilds)
            if guild is None:
                raise commands.GuildNotFound(argument)

            if TYPE_CHECKING:
                assert isinstance(guild, discord.Guild)

        try:
            member = await guild.fetch_member(ctx.author.id) # type: ignore
        except discord.HTTPException:
            raise commands.GuildNotFound(argument)

        if guild.me is not None:
            if not member.guild_permissions.manage_emojis or not guild.me.guild_permissions.manage_emojis:
                raise commands.GuildNotFound(argument)

        return guild

class EmojiNameConverter:
    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> str:
        emoji_name_regex = r"^(?P<name>[a-zA-Z0-9_]{2,32})$"
        match = re.match(emoji_name_regex, argument)
        if match:
            return match.group("name")

        raise commands.BadArgument(f"{argument} is not a valid emoji name.")

class EmojiTypeConverter:
    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> str:
        emoji_types = ("all", "static", "animated")
        if argument.lower() not in emoji_types:
            raise commands.BadArgument("Please specify a valid emoji type (all, animated or static)")

        return argument.lower()

