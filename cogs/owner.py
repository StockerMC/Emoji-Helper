from discord.ext import commands
import discord
import asyncio
import re
import traceback
import sys

class Owner(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def cog_check(self, ctx):
		return await self.bot.is_owner(ctx.author)

	@commands.command()
	async def servers(self, ctx):
		await ctx.send(f"{len(self.bot.guilds)} servers")

	@commands.command()
	async def members(self, ctx):
		await ctx.send(len(guild.member_count for guild in self.bot.guilds))

	@commands.command()
	async def reload(self, ctx, *, module):
		try:
			embed = discord.Embed(title=f"Reloading the cog `{module}`...", color=0xf9c94c)
			msg = await ctx.send(embed=embed)
			self.bot.reload_extension(f"cogs.{module}")
		except Exception as e:
			e = traceback.format_exception(type(e), e, e.__traceback__)
			embed = discord.Embed(title=f"Failed to reload the cog `{module}`", description=f"```{(''.join(e))[0:2048]}```", color=0x2683C9)
			await msg.edit(content=None, embed=embed)
		else:
			embed = discord.Embed(title=f"Successfully reloaded the cog `{module}`", color=0x27c43a)
			await msg.edit(content=None, embed=embed)

	@commands.command(aliases=["close", "restart"])
	async def stop(self, ctx):
		await ctx.send("Shutting down the bot...")
		await self.bot.close()
		exit_code = self.bot.config["systemd_exit_code"]
		sys.exit(exit_code)
		

	@commands.command(aliases=["sync"])
	async def pull(self, ctx, restart=False):
		await ctx.trigger_typing()
		process = await asyncio.create_subprocess_shell(
			"git pull",
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.PIPE
		)

		stdout, stderr = await process.communicate()
		stdout = f"{stdout.decode() if stdout is not None else ''}"
		stderr = f"{stderr.decode() if stderr is not None else ''}"

		matches = re.findall(r"cogs/([a-zA-Z0-9]+)\.py", stdout)
		for match in matches:
			try:
				self.bot.reload_extension(f"cogs.{match}")
			except Exception as e:
				stderr += f"\n{e}"

		reloaded_cogs = ", ".join(matches) if matches else None

		embed = discord.Embed(title="Pulling from GitHub...", description=f"```{stdout}\n{stderr}```", color=0xf9c94c)
		embed.add_field(name="Reloaded cogs", value=reloaded_cogs)
		await ctx.send(embed=embed)
		if restart:
			embed = discord.Embed(title="Restarting bot...", color=0xf9c94c)
			await ctx.send(embed=embed)
			await self.bot.close()

	@commands.command()
	async def pip(self, method, ctx, *, input):
		await ctx.trigger_typing()
		version = sys.version.split()[0][:-2]
		command = f"python{version} -m pip {method} {input}"
		process = await asyncio.create_subprocess_shell(
			command,
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.PIPE
		)

		stdout, stderr = await process.communicate()
		stdout = f"{stdout.decode() if stdout is not None else ''}"
		stderr = f"{stderr.decode() if stderr is not None else ''}"
		embed = discord.Embed(title=command, description=f"```{stdout}\n{stderr}```", color=self.bot.color)
		await ctx.send(embed=embed)

	@commands.group(invoke_without_command=True)
	async def sql(self, ctx, *, query):
		result = await self.bot.pool.execute(query.lstrip("```sql").rstrip("```"))
		await ctx.send(f"```\n{result}```")

	@sql.command()
	async def execute(self, ctx, *, query):
		await self.sql(ctx, query=query)

	@sql.command()
	async def fetch(self, ctx, *, query):
		result = await self.bot.pool.fetch(query.lstrip("```sql").rstrip("```"))
		await ctx.send(f"```\n{result}```")

	@commands.command(aliases=["usages"])
	async def uses(self, ctx, command=None):
		
		embed = discord.Embed(color=self.bot.color)
		if not command:
			embed.title = "Command uses of all commands"
			for name, uses in self.bot.command_uses.items():
				embed.add_field(name=name, value=f"{uses} use{'s' if uses != 1 else ''}")

			return await ctx.send(embed=embed)

		command = self.bot.get_command(command)
		if not command:
			embed = ctx.error("There is no command with that name")
			return await ctx.send(embed=embed)

		try:
			uses = self.bot.command_uses[command]
		except KeyError:
			self.bot.command_uses[command] = 0
			uses = 0

		embed = discord.Embed(title=f"Command uses of the command `{command}`", description=f"{uses} use{'s' if uses != 1 else ''}", color=self.bot.color)
		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(Owner(bot))