import discord
import os
import warnings
import logging
import json
from utils.bot import Bot, Help
from utils import database
import asyncio
import sys
import pkgutil

warnings.filterwarnings("error")

if sys.platform == "win32":
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

with open("data/config.json") as f:
	config = json.load(f)

if not config["database"]["setup_completed"]:
	import asyncio
	from utils.database import setup
	
	asyncio.create_task(setup(config))
	config["database"]["setup_completed"] = True
	with open("data/config.json", "w") as f:
		json.dump(config, f, indent=4)

os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"

bot = Bot(
	command_prefix=database.get_prefix,
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
	case_insensitive=True,
	help_command=Help(sort_commands=True),
	activity=discord.Game("e!help"),
	# prevents an initial API call for is_owner
	owner_id=323490082382282752,
	# disables the message cache
	max_messages=None,
	config=config
)

@bot.event
async def on_command(ctx):
	try:
		bot.command_uses[ctx.command.qualified_name] += 1
	except KeyError:
		bot.command_uses[ctx.command.qualified_name] = 1

for importer, name, ispkg in pkgutil.iter_modules(("cogs",)):
	bot.load_extension(f"cogs.{name}")

bot.load_extension("jishaku")

logging.basicConfig(level=logging.WARNING)
bot.run(config["bot"]["token"])