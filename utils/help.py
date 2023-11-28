# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

# TODO: make help command nicer

from __future__ import annotations

import discord
from discord.ext import commands
import textwrap
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from collections.abc import Mapping
    from utils import Bot, Context

# this was inspired by https://mystb.in/EthicalBasketballPoliticians.python by pikaninja
class HelpEmbed(discord.Embed):
    def __init__(self, ctx: Context, **kwargs):
        original_description = kwargs.get("description", "")
        notes = textwrap.dedent("""\
        ```
        <> = required
        [] = optional
        | = or
        ... = at least one
        ```
        """)
        description = f"{notes}\n{original_description}"
        kwargs["description"] = description
        kwargs["color"] = ctx.bot.color
        super().__init__(**kwargs)
        self.set_footer(text=f"Use {ctx.prefix}help [command] or {ctx.prefix}help [category] for more information")

# class Help(commands.MinimalHelpCommand): ## make better help command
#     async def send_pages(self):
#         destination = self.get_destination()
#         if self.paginator is not None:
#             for page in self.paginator.pages:
#                 embed = discord.Embed(description=page)
#                 await destination.send(embed=embed)

class HelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], list[commands.Command]]):
        return await super().send_bot_help(mapping)
