# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

import discord
from discord.ext import commands
from utils import Bot, Config
import asyncio
import sys
import asyncpg
import argparse
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    class GuildConfigRecord(asyncpg.Record, TypedDict):
        # guild_id: int
        prefix: str
        emojify_toggle: bool

async def get_prefix(bot: Bot, message: discord.Message):
    if message.guild:
        guild_config = await bot.get_guild_config(message.guild.id) # type: ignore
    else:
        guild_config = bot.default_guild_config

    prefix = guild_config["prefix"]

    if bot.mentionable:
        return commands.when_mentioned_or(prefix)(bot, message)
    else:
        return prefix

@asynccontextmanager
async def create_pool(**postgres_config):
    if not postgres_config.pop("use_database"):
        yield None

    else:
        async with asyncpg.create_pool(**postgres_config) as pool:
            yield pool

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-count", type=int, default=None, help="The total number of shards. Example: 10. This is optional.")
    parser.add_argument(
        "--shard-ids",
        type=str,
        default=None,
        help='An optional list of shard_ids to launch the shards with. These shard_ids should be in a string, separated by a space. Example: "1 2 3 4". This is optional.',
    )
    parser.add_argument("--config-file", type=str, default=None, help="The file path for the config file. This is optional.")
    args = parser.parse_args()

    shard_count = args.shard_count
    if shard_count is not None:
        shard_count = int(shard_count)

    shard_ids = args.shard_ids
    if shard_ids is not None:
        shard_ids = [int(id) for id in shard_ids.split()]

    config_file = args.config_file
    if config_file is None:
        config_file = "data/config.toml"
    config = Config(config_file)

    async with create_pool(**config.database) as pool:
        bot = Bot(
            command_prefix=get_prefix,
            intents=discord.Intents(
                # on_guild_* events and bot.guilds
                guilds=True,
                # necessary for commands to work in guilds and DMs
                messages=True,
                # reactions will never be listened for in DMs
                guild_reactions=True,
                # emoji related attributes and methods
                emojis=True
            ),
            # disables the message cache
            max_messages=None,
            # prevents the bot from mentioning anyone (including everyone and roles)
            allowed_mentions=discord.AllowedMentions.none(),
            shard_ids=shard_ids,
            shard_count=shard_count,
            config=config,
            pool=pool
        )

        try:
            await bot.start(config.bot.token)
        finally:
            # await bot.close() # is this necessary?
            exit_code = config.bot.exit_code
            if exit_code:
                sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
