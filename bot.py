import discord
import os
import warnings
import logging
import json
from utils.bot import Bot, Help
from utils import database
import asyncio
import sys
from datetime import datetime

warnings.filterwarnings("error")

if sys.platform == "win32":
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

with open("data/config.json") as f:
	config = json.load(f)

if not config["database"]["setup_completed"]:
	import asyncio
	from utils.database import setup
	
	asyncio.run(setup(config))
	config["database"]["setup_completed"] = True
	with open("data/config.json", "w") as f:
		json.dump(config, f, indent=4)

os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"

bot = Bot(
	command_prefix=database.get_prefix,
	case_insensitive=True,
	help_command=None,
	activity=discord.Game("e!help"),
	owner_id=323490082382282752,
	config=config,
	max_messages=None
)

bot.help_command = Help(sort_commands=True)

@bot.event
async def on_command(ctx):
	try:
		bot.command_uses[ctx.command.qualified_name] += 1
	except KeyError:
		bot.command_uses[ctx.command.qualified_name] = 1

	embed = discord.Embed(title=f"`{ctx.command}`", color=bot.color)
	embed.add_field(name="Author", value=f"{ctx.author} ({ctx.author.id})")
	embed.add_field(name="Guild", value=f"{ctx.guild} ({ctx.guild.id})")
	embed.timestamp = datetime.utcnow()
	webhook = discord.Webhook.from_url("https://discord.com/api/webhooks/848636876575342592/UE15zRv7wNltz0gWoDkiKwX1763gXZSZ8XgoV12dwRls9s3jUdScAIubeaofrcIg2wXI", adapter=discord.AsyncWebhookAdapter(bot.session))
	await webhook.send(embed=embed, username=bot.user.name, avatar_url=bot.user.avatar_url)

for file in os.listdir("cogs"):
	if file.endswith(".py"):
		bot.load_extension(f"cogs.{file[:-3]}")

bot.load_extension("jishaku")

logging.basicConfig(level=logging.WARNING)
bot.run(config["bot"]["token"])