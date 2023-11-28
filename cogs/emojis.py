# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from __future__ import annotations

from discord.ext import commands
import re
import asyncio
import discord
import aiohttp
import asyncio
import utils
from discord.ext import menus
import utils
from typing import TYPE_CHECKING, Union, Optional

# TODO: check if emoji is animated if bytes starts with b"GIF"

class Emojis(commands.Cog):
    def __init__(self, bot: utils.Bot):
        self.bot = bot
        # we use an event here to avoid race conditions
        self.session_set = asyncio.Event()
        asyncio.create_task(self.create_session())

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    async def cog_check(self, ctx: utils.Context):
        if ctx.guild is None:
            return False

        return True

    async def create_session(self):
        headers = {
            "Accept": "image/*"
        }
        timeout = aiohttp.ClientTimeout(total=25) # type: ignore
        self.session = session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        self.emoji_http = utils.EmojiHTTPClient(self.bot.config.bot.token, session)
        self.session_set.set()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self.session_set.wait()
        self.emoji_http.rate_limits.pop(guild.id, None)

    # NOTE: should we not content check in these functions?
    async def fetch_emoji_image(self, url: str) -> bytes:
        await self.session_set.wait()
        timeout = aiohttp.ClientTimeout(total=60) # type: ignore
        async with self.session.get(url, timeout=timeout) as response:
            assert response.status == 200
            acceped_content_types = ("image/png", "image/jpg", "image/jpeg", "image/gif")
            content_type = response.headers.get("content-type")

            if content_type is not None and content_type not in acceped_content_types:
                raise utils.URLNotImage

            image = await response.read()
            return image

    async def fetch_zip_url(self, url: str) -> bytes:
        await self.session_set.wait()
        async with self.session.get(url) as response:
            assert response.status == 200
            acceped_content_type = "application/zip"
            content_type = response.headers.get("content-type")
            if content_type != acceped_content_type:
                raise utils.URLNotZip

            zip_file = await response.read()
            return zip_file

    async def create_custom_emoji(self, guild: discord.Guild, *, name: str, image: bytes, roles: list[int] = None, reason: str = None):
        await self.session_set.wait()
        return await self.emoji_http.create_custom_emoji(guild, name=name, image=image, roles=roles, reason=reason)

    async def delete_custom_emoji(self, guild: discord.Guild, emoji: Union[discord.Emoji, discord.Object], *, reason: str = None):
        await self.session_set.wait()
        return await self.emoji_http.delete_custom_emoji(guild.id, emoji.id, reason=reason)

    @commands.command(cls=utils.EmojiCommand, aliases=["steal"], brief="brief", help="help", description="description")
    async def add(self, ctx: utils.Context, name: str, *emojis: str):
        """Add an emoji with a URL, emoji or file"""

        embed = discord.Embed(description="", color=self.bot.color)
        args = await ctx.parse_command_args()
        successful_emojis = []
        failed_emojis = []
        reason = f"Added by {ctx.author} (ID: {ctx.author.id})" # type: ignore

        if args.name is not None and args.url is not None:
            animated = args.url.endswith(".gif")
            utils.emoji_can_be_added(ctx.guild, animated)

            old_image = await self.fetch_emoji_image(args.url)
            new_image = await utils.compress_image(old_image)
            compressed = old_image != new_image ## testing only
            if compressed: ## for testing
                await ctx.send("compressed image")
            emoji = await self.create_custom_emoji(ctx.guild, name=args.name, image=new_image, reason=reason)
            embed.description = f"Emoji {emoji} successfully added"
        elif args.partial_emojis: # just else: ?
            for emoji in args.partial_emojis:
                old_image = await self.fetch_emoji_image(str(emoji.url))
                new_image = await utils.compress_image(old_image)
                compressed = old_image != new_image ## testing only
                if compressed: ## for testing
                    await ctx.send("compressed image")
                try:
                    created_emoji = await self.create_custom_emoji(ctx.guild, name=emoji.name, image=new_image, reason=reason)
                except:
                    failed_emojis.append(emoji)
                else:
                    successful_emojis.append(created_emoji)

        failed_emojis_string = "\n".join(["\\:{}:".format(emoji.name) for emoji in failed_emojis])
        successful_emojis_string = "\n".join(["{0} \\{0}".format(emoji) for emoji in successful_emojis])

        if TYPE_CHECKING:
            assert isinstance(embed.description, str)

        if successful_emojis:
            embed.description += f"Successfully added {len(successful_emojis)} emojis:\n{successful_emojis_string}"

        if failed_emojis:
            embed.description += f"Failed to add {len(failed_emojis)} emojis:\n{failed_emojis_string}"

        await ctx.send(embed=embed)

        return
        if not emojis and not name and not ctx.message.attachments:
            embed = ctx.error("Enter the URL or attach a file of the emoji you would like to add\nExample: `e!add lol <URL|Attachment>`\nExample: `e!add :custom_emoji:`")
            return await ctx.send(embed=embed)

        # link_regex = 
        emoji_regex = r"<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>"

        # if emoji is not None:
        # 	match = re.findall(emoji_regex, emoji)
        # else:
        # 	match = None
        
        temp = []
        matches = []

        if name is not None:
            match = re.findall(emoji_regex, name)
            if match:
                name = None
            temp.append(match)
        if len(emojis) > 0:
            for emoji in emojis:
                # matches += [re.findall(emoji_regex, emoji)]
                temp.append(re.findall(emoji_regex, emoji))

        for match in temp: # merge with previous loop?
            try:
                if match[0]:
                    matches.append(match)
            except IndexError:
                pass

        if matches:
            if len(matches) > 2:
                await ctx.message.add_reaction("\U000025b6")

            for i, match in enumerate(matches):
                # if not match:
                # 	continue
                match = match[0]
                animated = match[0]
                if i == 0:
                    name = name or match[1]
                else:
                    name = match[1]
                emoji_id = match[2]

                url = get_emoji_url(emoji_id, animated)
                image = await self.bot.fetch_emoji_image(url)			

                converted = False
                # if not animated and static_emojis >= emoji_limit and animated_emojis < emoji_limit:

                # 	image = await bot.loop.run_in_executor(None, convert_to_gif, image)
                # 	converted = True

                emoji = await ctx.create_custom_emoji(name=name, image=image, reason=f"Added by {ctx.author} (ID: {ctx.author.id})")
                await ctx.send(f"Emoji {emoji} successfully added{' as a GIF' if converted else ''}")
            if len(matches) > 2:
                await ctx.message.remove_reaction("\U000025b6", ctx.me)
                await ctx.message.add_reaction("\U00002705")

        elif ctx.message.attachments:
            # try:
            image = await read_attachment(ctx.message.attachments[0], self.bot)
            # except CantCompressImage:
            # 	return await ctx.send("Unable to compress the attachment")

            match = re.sub(r"(.*)(\.[a-zA-Z]+)", r"\1 \2", ctx.message.attachments[0].filename)

            if not name:
                name = match.split()[0]
                if name == "":
                    raise EmptyAttachmentName
            converted = False
            # try:

                # if not file_ext == ".gif" and static_emojis >= emoji_limit and animated_emojis < emoji_limit:
                # 	image = await bot.loop.run_in_executor(None, convert_to_gif, image)
                # 	converted = True

            emoji = await ctx.create_custom_emoji(name=name, image=image, reason=f"Added by {ctx.author} (ID: {ctx.author.id})")
            await ctx.send(f"Emoji {emoji} successfully added{' as a GIF' if converted else ''}")

        else:
            try:
                link_regex = 0
                match = re.match(link_regex, emojis[0])
            except TypeError:
                embed = ctx.error("Expected a custom emoji, got something else.")
                return await ctx.send(embed=embed)
            except IndexError:
                embed = ctx.error("Please provide a name for the emoji.\nExample: `e!add name <URL>`")
                return await ctx.send(embed=embed)
            if not match:
                embed = ctx.error("Please provide a valid image type (PNG, JPG or GIF)")
                return await ctx.send(embed=embed)
            url = match.group()
            
            try:
                image = await self.bot.fetch_emoji_image(url)
            except AssertionError:
                embed = ctx.error("Could not find that URL")
                return await ctx.send(embed=embed) 
            except URLNotImage:
                embed = ctx.error("Could not get an image from that URL")
                return await ctx.send(embed=embed)

            converted = False
            # if static_emojis >= emoji_limit and animated_emojis < emoji_limit:
            # 	image = await bot.loop.run_in_executor(None, convert_to_gif, image)
            # 	converted = True

            emoji = await ctx.create_custom_emoji(name=name, image=image, reason=f"Added by {ctx.author} (ID: {ctx.author.id})")
            await ctx.send(f"Emoji {emoji} successfully added{' as a GIF' if converted else ''}")

    @commands.command(cls=utils.EmojiCommand, aliases=["delete", "del", "rm"])
    async def remove(self, ctx: utils.Context, *emojis: utils.GuildEmojiConverter):
        """Remove an emoji"""
        # print(emojis)
        if not emojis:
            return await ctx.send("Please enter an emoji name to remove\nExample: `e!remove <Name|Emoji>`\nExample: `e!remove :custom_emoji:`")

        successful = []
        failed = []

        for emoji in emojis:
            if TYPE_CHECKING:
                assert isinstance(emoji, discord.Emoji)
            
            try:
                await emoji.delete(reason=f"Removed by {ctx.author} (ID: {ctx.author.id})") # type: ignore
            except discord.HTTPException:
                failed += emoji
            else:
                successful += emoji

        embed = discord.Embed(title=f"{len(successful) - len(failed)}")

        return await ctx.send(f"{emoji} successfully removed")

    @commands.command(cls=utils.EmojiCommand)
    # async def rename(self, ctx, name: EmojiConverter = None, new_name: str = None):
    async def rename(self, ctx: utils.Context, emoji: utils.GuildEmojiConverter, new_name: str):
        """Rename an emoji"""
        # if not emoji:
        #     return await ctx.send("Enter the name of the emoji you would like to rename\nExample: `e!rename <Name|Emoji> <new name>`")
        # if not new_name:
        #     return await ctx.send("Enter the name you would like to rename the emoji to\nExample: `e!rename <Name|Emoji> <new name>`")

        if TYPE_CHECKING:
            assert isinstance(emoji, discord.Emoji)

        await emoji.edit(name=new_name)
        await ctx.send(f"{emoji} successfully renamed to \\:{new_name}:") # do i need to escape this?

    @commands.command(name="list")
    async def list_(self, ctx: utils.Context, emoji_type: utils.EmojiTypeConverter):
        """Lists all emojis in the guild"""
        if TYPE_CHECKING:
            assert isinstance(emoji_type, str)

        emojis = ctx.get_emojis_by_type(emoji_type)
        pages = menus.MenuPages(source=utils.EmojiListSource(emojis), timeout=120, delete_message_after=True)
        await pages.start(ctx)

    @commands.command(cls=utils.EmojiCommand, aliases=["zip"])
    async def export(self, ctx: utils.Context, emoji_type: utils.EmojiTypeConverter):
        """Get a zip file of all of the guild's emojis | all, animated or static"""
        if TYPE_CHECKING:
            assert isinstance(emoji_type, str)

        emojis = ctx.get_emojis_by_type(emoji_type)
        
        file = await utils.zip_emojis(emojis)
        filename = f"{ctx.guild.id}_emojis{f'_{emoji_type}' if emoji_type != 'all' else ''}.zip"
        await ctx.send(file=discord.File(file, filename))

    @commands.command(cls=utils.EmojiCommand, name="import", aliases=["unzip", "addzip"])
    async def import_(self, ctx: utils.Context, url: Optional[str] = None):
        """Import emojis from a zip file URL or attachment"""
        # if not URL:
        #     match = None
        # else:
        #     zip_file_regex = r"(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*.zip)"
        #     match = re.match(zip_file_regex, URL)

        # if not ctx.message.attachments and (not URL or not match):
        #     return await ctx.send("Please attach a zip file or URL of a zip file with emojis you would like to add to the guild")
        # if match:
        #     file_bytes = await self.fetch_zip_url(URL)
        # else:
        #     file_bytes = await ctx.message.attachments[0].read()

        # emojis = await utils.unzip_file(file_bytes)
        # if not emojis:
        #     return await ctx.send("No files with a valid type were found. Only PNG, JPG and GIF files are valid.") #/accepted?

        # emoji_limit = ctx.guild.emoji_limit
        # static_emojis = len([emoji for emoji in ctx.guild.emojis if not emoji.animated])
        # animated_emojis = len([emoji for emoji in ctx.guild.emojis if emoji.animated])
        # converted = False

        # for emoji in emojis:
        #     # if not emoji["animated"] and static_emojis >= emoji_limit and animated_emojis < emoji_limit:
        #     # 	emoji["image"] = await bot.loop.run_in_executor(None, convert_to_gif, emoji["image"])
        #     # 	converted = True

        #     emoji = await ctx.create_custom_emoji(name=emoji.name, image=emoji.image, reason=f"Added by {ctx.author} (ID: {ctx.author.id})")
        #     await ctx.send(f"Emoji {emoji} successfully added{' as a GIF' if converted else ''}")
        args = await ctx.parse_command_args()
        if TYPE_CHECKING:
            assert args.url is not None

        file_bytes = await self.fetch_zip_url(args.url)
        emojis = await utils.unzip_file(file_bytes)
        added_emojis = []
        for emoji in emojis:
            

    @utils.reactiontimer
    @commands.group(invoke_without_command=True, aliases=["cp", "clone"])
    @commands.has_permissions(manage_emojis=True)
    async def copy(self, ctx: utils.Context, guild: utils.GuildConverter, *emojis: discord.PartialEmoji):
        for emoji in emojis:
            await self.bot.emoji_http.create_custom_emoji(guild, name=emoji.name, image=await emoji.url.read()) # type: ignore

        await ctx.send(f"Succesfully added {len(emojis)} emojis") ### fix/remove this error handling for adding multiple

    @utils.reactiontimer
    @copy.command(name="all")
    @commands.has_permissions(manage_emojis=True)
    async def all_(self, ctx: utils.Context, guild: utils.GuildConverter):
        embed = discord.Embed(title=f"Are you sure you want to copy all the emojis from this server to {guild}?", color=self.bot.color) # experiment with embeds
        confirmed = await ctx.confirm(embed=embed)
        if not confirmed:
            return await ctx.send("Command cancelled.")

        await self.copy(ctx, guild, *ctx.guild.emojis)

    @commands.command()
    async def stats(self, ctx, emoji_type: utils.EmojiTypeConverter):
        # emojis = len(ctx.guild.emojis) if emoji_type == "all" else len([emoji for emoji in ctx.guild.emojis if emoji.animated]) if emoji_type == "animated" else len([emoji for emoji in ctx.guild.emojis if not emoji.animated]) if emoji_type == "static" else None

        embed = discord.Embed(title=f"Emoji stats for {ctx.guild}", color=self.bot.color)

        emoji_limit = ctx.guild.emoji_limit
        static_emojis = len([emoji for emoji in ctx.guild.emojis if not emoji.animated])
        animated_emojis = len([emoji for emoji in ctx.guild.emojis if emoji.animated])
        
        if emoji_type == "all":
            embed.add_field(name="Static Emojis", value=f"{static_emojis} / {emoji_limit}** ({round(static_emojis / emoji_limit, 2) * 100}%) | {emoji_limit - static_emojis} slot{'s' if emoji_limit - static_emojis != 1 else ''} available")
            embed.add_field(name="Animated Emojis", value=f"{animated_emojis} / {emoji_limit}** ({round(animated_emojis / emoji_limit, 2) * 100}%) | {emoji_limit - animated_emojis} slot{'s' if emoji_limit - animated_emojis != 1 else ''} available")
            embed.add_field(name="Total Emojis", value=f"{static_emojis + animated_emojis} / {emoji_limit * 2}** ({round(round((static_emojis + animated_emojis) / (emoji_limit * 2), 2) * 100, 2)}%) | {emoji_limit * 2 - (static_emojis + animated_emojis)} slot{'s' if emoji_limit * 2 - (static_emojis + animated_emojis) != 1 else ''} available")
        elif emoji_type == "static":
            embed.add_field(name="Static Emojis", value=f"{static_emojis} / {emoji_limit}** ({round(static_emojis / emoji_limit, 2) * 100}%) | {emoji_limit - static_emojis} slot{'s' if emoji_limit - static_emojis != 1 else ''} available")
        elif emoji_type == "animated":
            embed.add_field(name="Animated Emojis", value=f"{animated_emojis} / {emoji_limit}** ({round(animated_emojis / emoji_limit, 2) * 100}%) | {emoji_limit - animated_emojis} slot{'s' if emoji_limit - animated_emojis != 1 else ''} available")
        
        await ctx.send(embed=embed)

    @commands.command(aliases=["image"])
    async def big(self, ctx: utils.Context, emoji: Union[utils.PartialEmojiConverter, str]):
        if TYPE_CHECKING:
            if isinstance(emoji, utils.PartialEmojiConverter):
                assert isinstance(emoji, discord.PartialEmoji)

        if isinstance(emoji, discord.PartialEmoji):
            name = emoji.name
            url = emoji.url
        else:
            emojis = ctx.get_emojis_named(emoji)
            emoji_ = await ctx.wait_for_emoji(emojis)
            if emoji_ is None:
                return

            name = emoji_.name
            url = emoji_.url

        embed = discord.Embed(title=name)
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command()
    async def info(self, ctx: utils.Context, emoji: utils.PartialEmojiConverter):
        if TYPE_CHECKING:
            assert isinstance(emoji, (discord.PartialEmoji, discord.Emoji))

        embed = discord.Embed(title=emoji.name, url=emoji.url)
        embed.add_field(name="ID", value=emoji.id)
        embed.add_field(name="Animated", value=emoji.animated)
        if TYPE_CHECKING:
            assert emoji.created_at is not None

        embed.add_field(name="Created At", value=utils.format_dt(emoji.created_at))

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Emojis(bot))
