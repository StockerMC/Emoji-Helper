from discord.ext import commands
import re
import io
from PIL import Image
import asyncio
import discord
from utils.zip import * # zip_emojis, fetch_zip_url
from utils.emoji import * # fetch_emoji_image, get_emoji_url, read_attachment
from utils.errors import EmptyAttachmentName

class Emojis(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def cog_check(self, ctx):
		return ctx.guild is not None

	def convert_to_gif(self, image_bytes):
		"""with io.BytesIO() as output:
			image = Image.open(io.BytesIO(image_bytes))
			image.save(output, format="GIF", **image.info)
			return output.getvalue()"""
		with io.BytesIO() as output:
			image = Image.open(io.BytesIO(image_bytes))

			image.save(output, save_all=True, append_images=[image.copy()], optimize=False, format="GIF", **image.info)

			# image.seek(0)
			# print(output.getvalue())
			# print(image.info)
			return output.getvalue()

	def gen_list(self, emojis, pages, current_page):
		current_emojis = emojis[(current_page-1)*10:current_page*10]
		description = ""
		for emoji in current_emojis:
			description += f"{emojis.index(emoji)+1}. {emoji} \\{emoji}\n"

		embed = discord.Embed(description=description)
		embed.set_footer(text=f"Page {current_page if current_page != 0 else 1} of {pages} | {len(emojis)} emojis")
		return embed

	@commands.command(aliases=["steal"])
	@commands.has_permissions(manage_emojis=True)
	async def add(self, ctx, name=None, *emojis):  # *args, split by space
		"""Add an emoji with a URL, emoji or file"""
		if not emojis and not name and not ctx.message.attachments:
			embed = ctx.error("Enter the URL or attach a file of the emoji you would like to add\nExample: `e!add lol <URL|Attachment>`\nExample: `e!add :custom_emoji:`")
			return await ctx.send(embed=embed)

		link_regex = r"(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
		emoji_regex = r"<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>"

		# if emoji is not None:
		# 	match = re.findall(emoji_regex, emoji)
		# else:
		# 	match = None
		
		temp = []
		matches = []

		if name is not None:
			temp.append(re.findall(emoji_regex, name))
		if len(emojis) > 0:
			for emoji in emojis:
				# matches += [re.findall(emoji_regex, emoji)]
				temp.append(re.findall(emoji_regex, emoji))

		for match in temp:
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
				image = await fetch_emoji_image(url, self.bot)			

				converted = False
				# if not animated and static_emojis >= emoji_limit and animated_emojis < emoji_limit:

				# 	image = await bot.loop.run_in_executor(None, convert_to_gif, image)
				# 	converted = True

				emoji = await safe_add_emoji(ctx.guild.create_custom_emoji(name=name, image=image, reason=f"Added by {ctx.author} (ID: {ctx.author.id})"))
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

			emoji = await safe_add_emoji(ctx.guild.create_custom_emoji(name=name, image=image, reason=f"Added by {ctx.author} (ID: {ctx.author.id})"))
			await ctx.send(f"Emoji {emoji} successfully added{' as a GIF' if converted else ''}")

		else:
			try:
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
				image = await fetch_emoji_image(url, self.bot)
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

			emoji = await safe_add_emoji(ctx.guild.create_custom_emoji(name=name, image=image, reason=f"Added by {ctx.author} (ID: {ctx.author.id})"))
			await ctx.send(f"Emoji {emoji} successfully added{' as a GIF' if converted else ''}")

	@commands.command(aliases=["delete", "del"])
	@commands.has_permissions(manage_emojis=True)
	async def remove(self, ctx, *emojis):
		"""Remove an emoji"""
		# print(emojis)
		if not emojis:
			return await ctx.send("Please enter an emoji name to remove\nExample: `e!remove <Name|Emoji>`\nExample: `e!remove :custom_emoji:`")
		emoji_regex = r"<a?:[a-zA-Z0-9_]{2,32}:(?P<id>[0-9]{18,22})>"
		matches = re.findall(emoji_regex, " ".join(emojis))
		if len(matches) > 2:
			await ctx.message.add_reaction("\U000025b6")
		if matches:
			for match in matches:
				emoji_id = match
				emoji = await ctx.guild.fetch_emoji(int(emoji_id)) # replace with Guild.delete_custom_emoji if added
				await emoji.delete(reason=f"Removed by {ctx.author} (ID: {ctx.author.id})")
				await ctx.send(f"{str(emoji)} successfully removed")
			
			await ctx.message.remove_reaction("\U000025b6", ctx.me)
			await ctx.message.add_reaction(self.bot.success_emoji)
		else:
			emojis_with_name = [
				[
					emoji for emoji in ctx.guild.emojis
					if emoji.name.lower() == name.lower()
				] for name in emojis
			][0]

			if len(emojis_with_name) == 0:
				return await ctx.send("This emoji does not exist") # change?

			if len(emojis_with_name) == 1:
				emoji = emojis_with_name[0]
				await emoji.delete(reason=f"Removed by {ctx.author} (ID: {ctx.author.id})")
				return await ctx.send(f"{emoji} successfully removed")

			else:
				msg = "Multiple emojis were found with that name.\nWhich emoji do you want to rename?\n"
				for i in range(len(emojis_with_name)):
					emoji = emojis_with_name[i-1]
					msg += f"{i+1}. {emoji}\n"
				msg = await ctx.send(msg)
				try:
					# message = await self.bot.wait_for("message", check=lambda m: m.channel == ctx.channel and m.author == ctx.author)
					message = await ctx.wait_for("message", timeout=120, numeric=True)
					try:
						emoji = emojis_with_name[int(message.content) - 1]
						await emoji.delete(reason=f"Removed by {ctx.author} (ID: {ctx.author.id})")
						await ctx.send(f"{emoji} successfully removed")
					except IndexError:
						return await ctx.send("This emoji does not exist")
				except asyncio.TimeoutError:
					return await msg.edit(content="This message has expired")  #change

	@commands.command()
	@commands.has_permissions(manage_emojis=True)
	async def rename(self, ctx, name=None, new_name=None):
		"""Rename an emoji"""
		if not name:
			return await ctx.send("Enter the name of the emoji you would like to rename\nExample: `e!rename <Name|Emoji> <new name>`")
		if not new_name:
			return await ctx.send("Enter the name you would like to rename the emoji to\nExample: `e!rename <Name|Emoji> <new name>`")

		emoji_regex = r"<a?:[a-zA-Z0-9_]{2,32}:(?P<id>[0-9]{18,22})>"
		match = re.findall(emoji_regex, name)
		if match:
			emoji_id = match.group("id")
			emoji = self.bot.get_emoji(int(emoji_id))
			if not emoji or emoji not in ctx.guild.emojis:
				return await ctx.send("This emoji does not exist")

			await emoji.edit(name=new_name, reason=f"Renamed by {ctx.author} (ID: {ctx.author.id})")
			await ctx.send(fr"{emoji} successfully renamed to \:{new_name}:")
		else:
			emojis_with_name = [
				emoji for emoji in ctx.guild.emojis
				if emoji.name.lower() == name.lower()
			]
			if len(emojis_with_name) == 0:
				return await ctx.send("This emoji does not exist")
			if len(emojis_with_name) == 1:
				await emojis_with_name[0].edit(name=new_name, reason=f"Renamed by {ctx.author} (ID: {ctx.author.id})")
				await ctx.send(fr"{emojis_with_name[0]} successfully renamed to \:{new_name}:")
			else:
				msg = "Multiple emojis were found with that name.\nWhich emoji do you want to rename?\n"
				for i in range(len(emojis_with_name)):
					emoji = emojis_with_name[i-1]
					msg += f"{i+1}. {emoji}\n"
				msg = await ctx.send(msg)
				try:
					# message = await self.bot.wait_for("message", check=lambda m: m.channel == ctx.channel and m.author == ctx.author)
					message = await ctx.wait_for("message", timeout=120, numeric=True)
					try:
						emoji = emojis_with_name[int(message.content) - 1]
						await emoji.edit(name=new_name, reason=f"Renamed by {ctx.author} (ID: {ctx.author.id})")
						await ctx.send(fr"{emoji} successfully renamed to \:{new_name}:")
					except IndexError:
						embed = ctx.error("This emoji does not exist")
						return await ctx.send(embed=embed)
				except asyncio.TimeoutError:
					return await msg.edit(content="This message has expired")  #change

	@commands.command(name="list")
	async def list_(self, ctx, emoji_type: lambda arg: arg.lower()="all"):
		"""Lists all emojis in the guild"""
		emojis = ctx.guild.emojis if emoji_type == "all" else [emoji for emoji in ctx.guild.emojis if emoji.animated] if emoji_type == "animated" else [emoji for emoji in ctx.guild.emojis if not emoji.animated] if emoji_type == "static" else None
		if not emojis:
			return await ctx.send("Please specify a valid emoji type (all, animated or static)")
		pages = round(len(emojis) / 10) if round(len(emojis) / 10) > 0 else 1
		current_page = 1
		embed = self.gen_list(emojis, pages, current_page)
		msg = await ctx.send(embed=embed)
		reactions = ["\U000023ee\U0000fe0f", "\U000023ea", "\U000023e9", "\U000023ed\U0000fe0f", "\U000023f9\U0000fe0f"]
		for reaction in reactions:
			await msg.add_reaction(reaction)

		while True:
			# reaction, user = await self.bot.wait_for("reaction_add", check=check) # timeout of 80?
			payload = await ctx.wait_for("raw_reaction_add", message=msg, reactions=reactions)
			if str(payload.emoji) == "\U000023ee\U0000fe0f":
				current_page = 1
				embed = self.gen_list(emojis, pages, current_page)
				await msg.edit(embed=embed)
			elif str(payload.emoji) == "\U000023ea":
				if current_page - 1 < 1:
					continue
				current_page -= 1
				embed = self.gen_list(emojis, pages, current_page)
				await msg.edit(embed=embed)
			elif str(payload.emoji) == "\U000023e9":
				if current_page + 1 > pages:
					continue
				current_page += 1
				embed = self.gen_list(emojis, pages, current_page)
				await msg.edit(embed=embed)
			elif str(payload.emoji) == "\U000023ed\U0000fe0f":
				current_page = pages
				embed = self.gen_list(emojis, pages, current_page)
				await msg.edit(embed=embed)
			else:
				return await msg.delete()

	@commands.command(aliases=["addthese"])
	@commands.has_permissions(manage_emojis=True)
	async def addmultiple(self, ctx, emojis: commands.Greedy[discord.PartialEmoji]=None):
		"""Add multiple emojis at once"""
		if not emojis:
			return await ctx.send("Enter the emojis you would like to add separated by a space\nExample: `e!addmultiple :emoji1: :emoji2:`")

		exceptions_raised = 0

		await ctx.message.add_reaction("\U000025b6")
		for emoji in emojis:
			try:
				await ctx.invoke(self.add, emoji.name, str(emoji.url))
			except discord.HTTPException as e:
				await ctx.send(str(e))
				exceptions_raised += 1

		await ctx.message.remove_reaction("\U000025b6", ctx.me)
		if exceptions_raised == len(emojis):
			await ctx.send("Could not add the emojis provided")
			return await ctx.message.add_reaction(self.bot.error_emoji)
		elif exceptions_raised > 0 and exceptions_raised < len(emojis):
			await ctx.send(f"Could not add {exceptions_raised / len(emojis)} emojis")
			return await ctx.message.add_reaction("\U000026a0")

		await ctx.message.add_reaction(self.bot.success_emoji)

	@commands.command(aliases=["removethese"])
	@commands.has_permissions(manage_emojis=True)
	async def removemultiple(self, ctx, emojis: commands.Greedy[discord.PartialEmoji]=None):
		"""Remove multiple emojis at once"""
		if not emojis:
			return await ctx.send("Enter the emojis you would like to remove separated by a space\nExample: `e!removemultiple :emoji1: :emoji2:`")

		for emoji in emojis:
			await ctx.invoke(self.remove, (str(emoji),))

	@commands.has_permissions(manage_emojis=True)
	@commands.command(aliases=["zip"])
	async def export(self, ctx, emoji_type: lambda arg: arg.lower()="all"):
		"""Get a zip file of all of the guild's emojis | all, animated or static"""
		emojis = ctx.guild.emojis if emoji_type == "all" else [emoji for emoji in ctx.guild.emojis if emoji.animated] if emoji_type == "animated" else [emoji for emoji in ctx.guild.emojis if not emoji.animated] if emoji_type == "static" else None
		if not emojis:
			return await ctx.send("Please specify a valid emoji type (all, animated or static)")
		
		file = await self.bot.loop.run_in_executor(zip_emojis, emojis)
		await ctx.send(file=discord.File(file, f"{ctx.guild.id}.zip"))

	@commands.has_permissions(manage_emojis=True)
	@commands.command(name="import", aliases=["unzip", "addzip"])
	async def import_(self, ctx, URL=None):
		"""Import emojis from a zip file URL or attachment"""
		link_regex = r"(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*.zip)"
		
		if not URL:
			match = None
		else:
			match = re.match(link_regex, URL)

		if not ctx.message.attachments and (not URL or not match):
			return await ctx.send("Please attach a zip file or URL of a zip file with emojis you would like to add to the guild")
		if match:
			file_bytes = await fetch_zip_url(URL, self.bot)
		else:
			file_bytes = await ctx.message.attachments[0].read()

		emojis = await self.bot.loop.run_in_executor(None, unzip_file, file_bytes)
		if not emojis:
			return await ctx.send("No files with a valid type were found. Only PNG, JPG and GIF files are valid.") #/accepted?

		emoji_limit = ctx.guild.emoji_limit
		static_emojis = len([emoji for emoji in ctx.guild.emojis if not emoji.animated])
		animated_emojis = len([emoji for emoji in ctx.guild.emojis if emoji.animated])
		converted = False

		for emoji in emojis:
			# if not emoji["animated"] and static_emojis >= emoji_limit and animated_emojis < emoji_limit:
			# 	emoji["image"] = await bot.loop.run_in_executor(None, convert_to_gif, emoji["image"])
			# 	converted = True

			emoji = await safe_add_emoji(ctx.guild.create_custom_emoji(name=emoji["name"], image=emoji["image"], reason=f"Added by {ctx.author} (ID: {ctx.author.id})"))
			await ctx.send(f"Emoji {emoji} successfully added{' as a GIF' if converted else ''}")

	@commands.command()
	async def stats(self, ctx, emoji_type: lambda arg: arg.lower()="all"):
		# emojis = len(ctx.guild.emojis) if emoji_type == "all" else len([emoji for emoji in ctx.guild.emojis if emoji.animated]) if emoji_type == "animated" else len([emoji for emoji in ctx.guild.emojis if not emoji.animated]) if emoji_type == "static" else None
		# if not emojis:
		# 	return await ctx.send("Please specify a valid emoji type (all, animated or static)")
		if emoji_type not in ["all", "static", "animated"]:
			embed = ctx.error("Please specify a valid emoji type (all, animated or static)")
			return await ctx.send(embed=embed)

		embed = discord.Embed(title=f"Emoji stats for {ctx.guild}", color=self.bot.color)

		emoji_limit = ctx.guild.emoji_limit
		static_emojis = len([emoji for emoji in ctx.guild.emojis if not emoji.animated])
		animated_emojis = len([emoji for emoji in ctx.guild.emojis if emoji.animated])
		
		if emoji_type == "all":
			embed.add_field(name="Static Emojis", value=f"{static_emojis} / {emoji_limit}** ({round(static_emojis / emoji_limit, 2) * 100}%) | {emoji_limit - static_emojis} slot{'s' if emoji_limit - static_emojis != 1 else ''} available")
			embed.add_field(name="Animated Emojis", value=f"{animated_emojis} / {emoji_limit}** ({round(animated_emojis / emoji_limit, 2) * 100}%) | {emoji_limit - animated_emojis} slot{'s' if emoji_limit - animated_emojis != 1 else ''} available")
			embed.add_field("Total Emojis", value=f"{static_emojis + animated_emojis} / {emoji_limit * 2}** ({round(round((static_emojis + animated_emojis) / (emoji_limit * 2), 2) * 100, 2)}%) | {emoji_limit * 2 - (static_emojis + animated_emojis)} slot{'s' if emoji_limit * 2 - (static_emojis + animated_emojis) != 1 else ''} available")
		elif emoji_type == "static":
			embed.add_field(name="Static Emojis", value=f"{static_emojis} / {emoji_limit}** ({round(static_emojis / emoji_limit, 2) * 100}%) | {emoji_limit - static_emojis} slot{'s' if emoji_limit - static_emojis != 1 else ''} available")
		elif emoji_type == "animated":
			embed.add_field(name="Animated Emojis", value=f"{animated_emojis} / {emoji_limit}** ({round(animated_emojis / emoji_limit, 2) * 100}%) | {emoji_limit - animated_emojis} slot{'s' if emoji_limit - animated_emojis != 1 else ''} available")
		
		await ctx.send(embed=embed)

	# @commands.command(hidden=True)
	# @commands.is_owner()
	# async def removeall(self, ctx, name):
	# 	for emoji in [emoji for emoji in ctx.guild.emojis if emoji.name.lower() == name]:
	# 		await self.remove(ctx, str(emoji))

def setup(bot):
    bot.add_cog(Emojis(bot))