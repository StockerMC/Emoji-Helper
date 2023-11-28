# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from __future__ import annotations

from discord.ext import commands
import discord
import textwrap
import string
import utils
from typing import TYPE_CHECKING

class Misc(commands.Cog):
    def __init__(self, bot: utils.Bot):
        self.bot = bot

    async def emojify_check(ctx: utils.Context): # type: ignore
        guild_config = await ctx.bot.get_guild_config(ctx.guild.id)
        emojify_toggle = guild_config["emojify_toggle"]
        if not emojify_toggle:
            raise utils.EmojifyDisabled

        return True

    def format_letters(self, letters: str) -> str:
        emoji_format = ":regional_indicator_{}: "
        numbers = {
            "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
        }
        message = ""

        for letter in letters:
            if letter.lower() in string.ascii_lowercase:
                message += emoji_format.format(letter.lower())
            elif letter in numbers.keys():
                message += f":{numbers[letter]}: "
            elif letter == " ":
                message += "   "
            else:
                message += f"{letter} "

        return message

    # TODO: remove guild only and make it show default prefix in dms?
    @commands.guild_only()
    @commands.command()
    async def prefix(self, ctx: utils.Context, prefix: str = None):
        """Show or change the bot's prefix for the guild"""
        if prefix:
            if not self.bot.use_database:
                return await ctx.send("You can't change the prefix for the bot.")

            if TYPE_CHECKING:
                assert isinstance(ctx.author, discord.Member)

            if ctx.author.guild_permissions.manage_emojis:
                await self.bot.change_prefix(ctx.guild.id, prefix)
                await ctx.send(f"The prefix for this guild has been changed to {prefix}")
            else:
                raise commands.MissingPermissions(["manage_emojis"])
        else:
            guild_config = await self.bot.get_guild_config(ctx.guild.id)
            await ctx.send(f"The prefix for this guild is {guild_config['prefix']}")

    @commands.command()
    async def ping(self, ctx: utils.Context):
        """Show the bot's latency"""

        message: discord.Message = await ctx.send("Pong!")
        delay = int((message.created_at - ctx.message.created_at).total_seconds() * 1000)
        await message.edit(content=f"Pong! `{delay}`ms\nWebsocket") # use embed with websocket api message latency

    @commands.command(aliases=["inv"])
    async def invite(self, ctx: utils.Context):
        """Get the invite link for the bot"""

        if TYPE_CHECKING:
            assert self.bot.user is not None

        invite = discord.utils.oauth_url(self.bot.user.id, discord.Permissions(1073794112))
        await ctx.send(f"<{invite}>")

    @commands.command()
    async def support(self, ctx: utils.Context):
        """Get the invite for the support server"""	
        try:
            await ctx.author.send(f"Official support server invite: {self.bot.support_server_invite}")
            await ctx.message.add_reaction(self.bot.success_emoji)
        except discord.Forbidden:
            await ctx.send(f"Cannot DM {str(ctx.author)}")
            await ctx.message.add_reaction(self.bot.error_emoji)

    @commands.group(invoke_without_command=True)
    @commands.check(emojify_check)
    async def emojify(self, ctx: utils.Context, *, letters: str = None):
        """Turn letters into emojis"""
        if not letters:
            return await ctx.send("Enter the letters you would like to emojify\nExample: `e!emojify emoji helper`")

        message = self.format_letters(letters)
        await ctx.send(message)

    @emojify.command()
    @commands.has_permissions(manage_emojis=True)
    async def toggle(self, ctx: utils.Context):
        """Toggle the use of the emojify command"""
        toggle_type = await self.bot.toggle_emojify(ctx.guild.id)
        await ctx.send(f"The emojify command is now {'enabled' if toggle_type else 'disabled'}")

    @commands.command()
    async def source(self, ctx: utils.Context):
        description = textwrap.dedent(f"""\
            Repository: {self.bot.repository_url}
            License: [EUPL-1.2](https://choosealicense.com/licenses/eupl-1.2/)

            As per the license, if you modify the source code you must make your bot open source and put it's repository URL in the config file.
        """)
        embed = discord.Embed(title="The Bot's Repository", description=description)
        await ctx.send(embed=embed)

    @commands.command()
    async def uptime(self, ctx: utils.Context):
        await ctx.send(f"I was started {utils.format_dt(self.bot.start_time, 'R')}")

def setup(bot: utils.Bot):
    bot.add_cog(Misc(bot))

    # this changes the help attribute for the command and disables the emojify toggle command
    # if use_database is set to false in the config
    if not bot.use_database:
        command = bot.get_command("prefix")
        if TYPE_CHECKING:
            assert isinstance(command, commands.Command)

        command.update(help="Show the bot's prefix for the guild")

        command = bot.get_command("emojify toggle")
        if TYPE_CHECKING:
            assert isinstance(command, commands.Command)

        command.update(enabled=False)
