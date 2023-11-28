# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from __future__ import annotations

import logging
import asyncio
import discord
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.config import ConfigNamespace
    from aiohttp import ClientSession

class WebhookHandler(logging.Handler):
    def __init__(self, level: logging._Level, logging_config: ConfigNamespace, session: ClientSession, format: str, print: bool):
        super().__init__(level)

        self.webhook = None
        webhook_url = logging_config.webhook_url
        if webhook_url:
            self.webhook = discord.Webhook.from_url(webhook_url, adapter=discord.AsyncWebhookAdapter(session))

        self.print = print
        formatter = logging.Formatter(fmt=format, style="{")
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord):
        message = self.format(record)

        if self.webhook is not None:
            asyncio.create_task(self.webhook.send(f"`{message}`"))

        if self.print:
            print(message)
