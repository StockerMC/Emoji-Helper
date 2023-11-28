# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from __future__ import annotations

from discord.ext import commands
import discord
import aiohttp
from .errors import *
from zipfile import BadZipFile
import traceback
import logging
import datetime
import re
import os
import humanize
from .context import Context
from .help import HelpCommand
from contextlib import asynccontextmanager
from .cache import alru_cache
from typing import TYPE_CHECKING, Optional, Type

if TYPE_CHECKING:
    from .config import Config
    from bot import GuildConfigRecord
    from asyncpg import Pool

class Bot(commands.AutoShardedBot):
    def __init__(self, *, config: Config, pool: Optional[Pool], **kwargs):
        self.config = config
        self.pool = pool

        self.default_prefix: str = self.config.prefix.default_prefix
        self.mentionable: bool = self.config.prefix.mentionable
        self.use_database = self.config.database.use_database

        activity = self.config.bot.activity
        if activity:
            activity = discord.Game(activity.format(prefix=self.default_prefix))
            kwargs["activity"] = activity

        kwargs["case_insensitive"] = self.config.bot.case_insensitive
        kwargs["help_command"] = HelpCommand()
        super().__init__(**kwargs)

        initial_extensions = (
            "cogs.emojis",
            "cogs.misc",
        )

        for extension in initial_extensions:
            self.load_extension(extension)

        for key, value in self.config.jishaku.items():
            os.environ[f"JISHAKU_{key}"] = value

        try:
            self.load_extension("jishaku")
        except commands.ExtensionError: # should we log here?
            pass
            # logging.warning("Could not load the jishaku extension")

        self.support_server_invite: str = self.config.bot.support_server_invite or "https://discord.gg/Y7S66uCfqq"
        self.success_emoji: str = self.config.emojis.success or "\U00002705"
        self.error_emoji: str = self.config.emojis.error or "\U0000274c"
        self.arrow_emoji: str = self.config.emojis.arrow or "\U000025b6\U0000fe0f"
        self.color: discord.Colour = self.config.bot.color
        self.default_guild_config: GuildConfigRecord = {
            "prefix": self.default_prefix,
            "emojify_toggle": True
        }
        self.repository_url: str = self.config.license.repository_url

        self.guild_log_channel_id = self.config.channels.guild_log
        self.traceback_channel_id = self.config.channels.traceback_channel

    """
    https://github.com/GenericDiscordBot/Generic-Bot/commit/f002e9894765dd9cd989c72ad947e43c3bf58271#diff-d2af56c0ebcc5288dbee11bd6edfb8a361634aaaa1851ef33850255db1f6790bR50-R55

    The following function is used under the following license:

    MIT License

    Copyright (c) 2021 Zomatree

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

    """

    @asynccontextmanager
    async def acquire(self):
        if self.pool is not None:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    yield connection

    async def get_context(self, message: discord.Message, *, cls=None) -> Context: # we set the cls kwarg for things like jishaku that use this method
        return await super().get_context(message, cls=Context)

    async def on_ready(self):
        self.start_time = datetime.datetime.now()

        if TYPE_CHECKING:
            assert self.user is not None
        
        print(f"{self.user.name} is now online!")

    @alru_cache
    async def get_guild_config(self, guild_id: int) -> GuildConfigRecord:
        if self.use_database:
            if TYPE_CHECKING:
                assert self.pool is not None

            async with self.acquire() as con:
                await con.execute("""
                    INSERT INTO guilds
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guild_id)
                    DO NOTHING
                """, guild_id, self.default_prefix, False)

                guild_config = await con.fetchrow("""
                    SELECT * FROM guilds
                    WHERE guild_id = $1
                """, guild_id)

            if TYPE_CHECKING:
                assert isinstance(guild_config, GuildConfigRecord)

            return guild_config
        else:
            return self.default_guild_config

    async def change_prefix(self, guild_id: int, prefix: str):
        if TYPE_CHECKING:
            assert self.pool is not None

        record = await self.pool.fetchrow("""
            UPDATE guilds
            SET prefix = $2
            WHERE guild_id = $1
            RETURNING *
        """, guild_id, prefix)

        self.get_guild_config.set_key(guild_id, record)
    
    async def delete_guild_config(self, guild_id: int):
        if TYPE_CHECKING:
            assert self.pool is not None

        record = await self.pool.execute("""
            DELETE FROM guilds
            WHERE guild_id = $1
        """, guild_id)

        self.get_guild_config.invalidate(guild_id)

    async def toggle_emojify(self, guild_id: int) -> bool:
        if TYPE_CHECKING:
            assert self.pool is not None

        record = await self.pool.fetchrow("""
                UPDATE guilds
                SET emojify_toggle = not emojify_toggle
                WHERE guild = $1
                RETURNING *
            """, guild_id)

        if TYPE_CHECKING:
            assert isinstance(record, GuildConfigRecord)

        self.get_guild_config.set_key(guild_id, record)
        return record["emojify_toggle"]

    async def on_guild_join(self, guild: discord.Guild):
        channel = self.get_channel(self.guild_log_channel_id)
        if channel is not None:
            await channel.send(f"The bot has been added to `{guild}`. The bot is now in `{len(self.guilds)}` servers")

    async def on_guild_remove(self, guild: discord.Guild):
        await self.delete_guild_config(guild.id)

        channel = self.get_channel(self.guild_log_channel_id)
        if channel is not None:
            await channel.send(f"The bot has been removed from `{guild}`. The bot is now in `{len(self.guilds)}` servers")

    async def on_command_error(self, ctx: Context, error: commands.CommandError): ## fix error handling
        error = getattr(error, "original", error)

        embed = ctx.command_error()

        match = re.search(r"Maximum number of(?P<animated> animated)? emojis reached \((?P<amount>\d+)\)", str(error))

        if isinstance(error, (commands.CommandNotFound, commands.BadArgument)):
            embed.description = str(error)

        elif isinstance(error, (commands.MissingRequiredArgument, CouldntConvertCommandArgs)):
            return await ctx.send_help(ctx.command)

        # merge these next 2?
        elif isinstance(error, commands.MissingPermissions):
            embed.description = f"You do not have permission to do this.\nMissing permissions: {', '.join(perm.replace('_', ' ').title() for perm in error.missing_perms)}"

        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = f"I do not have permissions to do this.\nMissing permissions: {', '.join(perm.replace('_', ' ').title() for perm in error.missing_perms)}"

        elif isinstance(error, commands.NoPrivateMessage):
            embed.description = "This command can only be used in a server."

        # elif isinstance(error, commands.NotOwner):
        # 	embed.description = "This command is only usable by the bot owner."

        elif isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            delta = datetime.timedelta(minutes=minutes, seconds=seconds)
            embed.description = f"This command is on cooldown for {humanize.precisedelta(delta)}."

        elif isinstance(error, commands.EmojiNotFound):
            embed.description = f"\\{error.argument} is not in this server or doesn't exist."

        elif isinstance(error, commands.PartialEmojiConversionFailure):
            embed.description = f"\\{error.argument} doesn't exist." # is not a valid emoji instead of doesn't exist; reword?

        elif isinstance(error, commands.GuildNotFound):
            embed.description = f"You or I do not have manage emoji permissions in the server {error.argument} or it does not exist." # comma after arg?

        elif isinstance(error, commands.DisabledCommand):
            embed.description = "This command is disabled."

        elif isinstance(error, RateLimited):
            command = ctx.command.parent or ctx.command
            assert isinstance(command, commands.Command)
            parent: str = command.name
            method = f"{parent.rstrip('e')}ing" # laziness
            minutes, seconds = divmod(error.retry_after, 60)
            delta = datetime.timedelta(minutes=minutes, seconds=seconds)
            embed.description = f"Discord told me to stop {method} emojis in this server for {humanize.precisedelta(delta)}."

        elif isinstance(error, EmojifyDisabled):
            embed.description = "This command is disabled in the server."

        elif isinstance(error, BadZipFile):
            embed.description = "The file provided was not a zip file, or it was an invalid zip file."

        elif isinstance(error, AssertionError):
            embed.description = "The URL provided was invalid."

        elif isinstance(error, URLNotImage):
            embed.description = "Could not get an image from the URL provided."

        elif isinstance(error, CantCompressImage):
            embed.description = "Could not compress this image. Please provide a smaller image when using the command again." # reword?

        elif isinstance(error, EmptyAttachmentName):
            embed.description = "The attachment provided did not have a name and no name was provided."

        elif match is not None:
            animated = match.group("animated")
            amount = match.group("amount")
            embed.description = f"Maximum number of {'animated' if animated else 'static'} emojis reached ({amount})."
        
        elif "validation regex" in str(error):
            embed.description = "The emoji name provided was invalid."

        # NOTE: remove this because of image compression?
        elif "In image: File cannot be larger than 256.0 kb." in str(error) or isinstance(error, ResourceWarning): # NOTE: will the isinstance even work lmao | replace with just 256.0 kb?
            embed.description = "The emoji image cannot be larger than 256 kb."

        else:
            traceback_channel: Optional[discord.TextChannel] = self.get_channel(self.traceback_channel_id)

            if isinstance(error, discord.Forbidden):
                missing_perms = []
                me = ctx.guild.me
                if me is not None:
                    permissions = me.permissions_in(ctx.channel)
                    if not permissions.send_messages:
                        return
                    if not me.guild_permissions.manage_emojis and ctx.command.name in ("add", "remove", "rename", "addmultiple", "removemultiple"):
                        missing_perms.append("Manage Emojis")
                    if not permissions.embed_links:
                        missing_perms.append("Embed Links")
                        return await ctx.send(f"I do not have permissions to do this.\nMissing permissions: {', '.join(missing_perms)}")

                embed.description = f"I do not have permissions to do this.\nMissing permissions: {', '.join(missing_perms)}"

            if traceback_channel is not None:
                traceback_string = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                traceback_embed = ctx.command_error(traceback_string)
                traceback_embed.add_field(name="Command Message", value=ctx.message.content)
                if ctx.message.attachments:
                    traceback_embed.add_field(name="Number of attachments", value=len(ctx.message.attachments))

                await traceback_channel.send(traceback_channel)

            embed.description = f"An unknown error happened:\n\n```{str(error)}```"

            if self.support_server_invite:
                embed.description += f"\nIf you need any help, feel free to join the [support server]({self.support_server_invite})"

        await ctx.send(embed=embed)

    async def on_error(self, event_method, *args, **kwargs):
        traceback_string = traceback.format_exc()
        embed = discord.Embed(description=f"```py\n{traceback_string}```")
        channel = self.get_channel(self.traceback_channel_id)
        if channel is not None:
            await channel.send(embed=embed)
