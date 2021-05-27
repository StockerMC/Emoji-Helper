import discord
import os
import warnings
import logging
import json
from utils.bot import Bot, Help
from utils import database
import asyncio
import sys

warnings.filterwarnings("error")

if sys.platform == "win32":
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

with open("data/config.json") as f:
	config = json.load(f)

if not config["database"]["setup_completed"]:
	import asyncio
	from utils.database import setup
	
	asyncio.get_event_loop().run_until_complete(setup(config))
	config["database"]["setup_completed"] = True
	with open("data/config.json", "w") as f:
		json.dump(config, f, indent=4)

os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True" 
os.environ["JISHAKU_HIDE"] = "True"

bot = Bot(command_prefix=database.get_prefix, case_insensitive=True, help_command=None, activity=discord.Game("e!help"), owner_id=323490082382282752, config=config)
bot.help_command = Help(sort_commands=True)

for file in os.listdir("cogs"):
	if file.endswith(".py"):
		bot.load_extension(f"cogs.{file[:-3]}")

bot.load_extension("jishaku")

logging.basicConfig(level=logging.WARNING)
bot.run(config["bot"]["token"])