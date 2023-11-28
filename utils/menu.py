# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from discord.ext import menus
import discord
from typing import TYPE_CHECKING, Sequence, Any

class EmojiListSource(menus.ListPageSource):
    def __init__(self, entries: Sequence[Any], *, title: str = "", description: str = ""):
        super().__init__(entries, per_page=10)
        self.title = title
        self.description = description

    async def format_page(self, menu: menus.MenuPages, entries: Any):
        offset = menu.current_page * self.per_page
        embed = discord.Embed(title=self.title, description=self.description)
        embed.set_footer(text=f"Page {menu.current_page + 1} of {self.get_max_pages()} | {len(self.entries)} emojis")

        for i, emoji in enumerate(entries, start=offset):
            if TYPE_CHECKING:
                assert isinstance(embed.description, str)

            embed.description += f"{i}. {emoji} \\{emoji}\n"

        return embed
