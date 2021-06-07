import asyncpg
from typing import Any

async def setup(config: dict[str, Any]):
	del config["database"]["setup_completed"]
	postgres_config = config["database"]
	async with asyncpg.create_pool(**postgres_config) as pool:
		async with pool.acquire() as con:
			async with con.transaction():
				with open("data/schema.sql") as f:
					await con.execute(f.read())