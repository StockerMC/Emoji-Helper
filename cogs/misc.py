from discord.ext import commands
import discord
import time
import re
import io
import asyncio
from discord.ext.commands.cooldowns import BucketType
from utils import database
from utils.emoji import fetch_emoji_image
from utils.errors import EmojifyDisabled

class Misc(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=["emoji", "image"])
	async def big(self, ctx, emoji=None):
		"""Enlarges an emoji"""
		if emoji is None:
			return await ctx.send("Enter the emoji you would like to enlarge\nExample: `e!big :emoji:`")
		
		emoji_regex = r"^<(a)?:(.+)?:(\d+)>$"
		match = re.findall(emoji_regex, emoji)
		# if match is None:
		# 	return await ctx.send("Expected a custom emoji, got something else")
		if match:
			match = match[0]
			animated = match[0]
			name = match[1]
			emoji_id = match[2]
			url = self.bot.get_emoji_url(emoji_id, animated)
			image = await fetch_emoji_image(url, self.bot)
			await ctx.send(file=discord.File(io.BytesIO(image), f"{name}.{'gif' if animated else 'png'}"))
		else:
			emojis_with_name = [
				emoji for emoji in ctx.guild.emojis
				if emoji.name.lower() == emoji.lower()
			]
			if len(emojis_with_name) == 0:
				return await ctx.send("This emoji does not exist")
			if len(emojis_with_name) == 1:
				emoji = emojis_with_name[0]
				animated = emoji.animated
				image = await fetch_emoji_image(str(emojis_with_name[0].url), self.bot)
				await ctx.send(file=discord.File(io.BytesIO(image), f"{emoji.name}.{'gif' if animated else 'png'}"))
			else:
				msg = "Multiple emojis were found with that name.\nWhich emoji do you want to enlarge?\n"
				for i in range(len(emojis_with_name)):
					emoji = emojis_with_name[i-1]
					msg += f"{i+1}. {str(emoji)}\n"
				msg = await ctx.send(msg)
				try:
					message = await self.bot.wait_for("message", check=lambda m: m.channel == ctx.channel and m.author == ctx.author)
					try:
						emoji = emojis_with_name[int(message.content) - 1]
						animated = emoji.animated
						url = self.bot.get_emoji_url(emoji.id, animated)
						image = await fetch_emoji_image(url, self.bot)
						await ctx.send(file=discord.File(io.BytesIO(image), f"{emoji.name}.{'gif' if animated else 'png'}"))
					except IndexError:
						return await ctx.send("This emoji does not exist")
				except asyncio.TimeoutError:
					return await msg.edit(content="This message has expired")  #change
	
	@commands.guild_only()
	@commands.command()
	async def prefix(self, ctx, prefix=None):
		"""Show or change the prefix for the guild"""
		if prefix:
			if ctx.author.guild_permissions.manage_emojis:
				await database.change_prefix(ctx.guild.id, prefix, self.bot)
				await ctx.send(f"The prefix for this guild has been changed to {prefix}", allowed_mentions=discord.AllowedMentions.none())
			else:
				raise commands.MissingPermissions(["manage_emojis"])
		else:
			prefix = await database.get_guild_prefix(ctx.guild.id, self.bot)
			await ctx.send(f"The prefix for this guild is {prefix}", allowed_mentions=discord.AllowedMentions.none())

	@commands.command()
	async def ping(self, ctx):
		"""Show the bot's ping"""
		start = time.time()
		delay = await ctx.send("Pinging...")
		ws_latency = round((time.time() - start) * 1000)
		api_latency = f"{ctx.bot.latency * 1000:.0f}"
		await delay.edit(content=f"WebSocket Latency: {ws_latency}ms\nAPI Latency: {api_latency}ms")

	@commands.command(aliases=["inv"])
	async def invite(self, ctx):
		"""Get the invite link for the bot"""
		invite = discord.utils.oauth_url(self.bot.user.id, discord.Permissions(1074088960))
		await ctx.send(f"<{invite}>")

	@commands.command()
	async def support(self, ctx):
		"""Get the invite for the support server"""	
		try:
			await ctx.author.send(f"Official support server invite: {self.bot.support_server}")
			await ctx.message.add_reaction(self.bot.success_emoji)
		except discord.Forbidden:
			await ctx.send(f"Cannot DM {str(ctx.author)}")
			await ctx.message.add_reaction(self.bot.error_emoji)

	@commands.group(invoke_without_command=True)
	async def emojify(self, ctx, *, letters=None):
		"""Turn letters into emojis"""
		state = await database.get_emojify(ctx.guild.id, self.bot)
		if not state:
			raise EmojifyDisabled()

		if letters is None:
			return await ctx.send("Enter the letters you would like to emojify\nExample: `e!emojify emoji helper`")
		if letters == False:
			return await ctx.send("You are not allowed to emojify that")
		emoji_prefix = ":regional_indicator_"
		# emoji_regex = r"^<?a?:.+?:\d+?>?$"
		alphabet = "abcdefghijklmnopqrstuvwxyz"
		numbers = {
			"1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
		}
		msg = ""
		for letter in letters:
			if letter.lower() in alphabet:
				msg += f"{emoji_prefix}{letter.lower()}: "
			elif letter in numbers.keys():
				msg += f":{numbers[letter]}: "
			elif letter == " ":
				msg += "   "
			else:
				msg += f"{letter} "
		
		#msg = " ".join([f"{'{}{}:'.format((emoji_prefix, letter.lower()) if letter.lower() is not in list(punctuation) else (letter.lower())) if letter != ' ' else '  '}" for letter in letters])
		await ctx.send(msg, allowed_mentions=discord.AllowedMentions.none())

	@emojify.command()
	@commands.has_permissions(manage_emojis=True)
	async def toggle(self, ctx):
		"""Toggle the use of the emojify command"""
		toggle_type = await database.toggle_emojify(ctx.guild.id, self.bot)
		await ctx.send(f"The emojify command is now {toggle_type}")

	@commands.command()
	async def faq(self, ctx):
		"""Shows the bot's FAQ"""
		await ctx.send("""**Why isn't the bot responding when I try to add/rename/remove emojis?**

When this happens, it means that the guild you are trying to do that in is rate limited (for emojis), meaning that the bot nor any other members can add/rename/remove emojis. 

Unfortunately, the **only **solution is to wait it out.""")

	@commands.command()
	@commands.cooldown(1, 10, BucketType.user)
	async def bug(self, ctx, *, message=None):
		"""Report a bug/issue with the bot"""
		if message is None:
			return await ctx.send("Please attach a message with the bug or issue you are experiencing.")
		channel = self.bot.get_channel(self.bot.bug_channel)
		embed = discord.Embed(title=f"Bug reported by {ctx.author}",color=0xd63636, description=message)
		await channel.send(embed=embed)
		await ctx.send("<:success:835736813929758740> Bug successfully reported")

def setup(bot):
    bot.add_cog(Misc(bot))