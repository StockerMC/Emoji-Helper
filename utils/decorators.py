# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from __future__ import annotations

import functools
import asyncio
import discord
from typing import TYPE_CHECKING, TypeVar, Any, Optional

if TYPE_CHECKING:
    from collections.abc import Callable, Awaitable
    from typing_extensions import ParamSpec
    from .context import Context

    P = ParamSpec("P")
    T = TypeVar("T")


# def executor() -> Callable[[Callable[P, T]], Callable[P, Awaitable[T]]]:
# 	def decorator(func: Callable[P, T]) -> Callable[P, Awaitable[T]]:
# 		@functools.wraps(func)
# 		def wrapper(*args: P.args, **kwargs: P.kwargs) -> Coroutine[Any, Any, T]:
# 			return asyncio.to_thread(func, *args, **kwargs)

# 		return wrapper

# 	return decorator

def executor(func: Callable[P, T]) -> Callable[P, Awaitable[T]]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Awaitable[T]:
        return asyncio.to_thread(func, *args, **kwargs)

    return wrapper

async def try_add_reaction(message: discord.Message, emoji: str) -> bool:
    try:
        await message.add_reaction(emoji)
        return True
    except discord.HTTPException:
        return False

"""
https://github.com/Gorialis/jishaku/commit/350b5176703790dded51280acd97e767a7fa4591#diff-7eb7d8e73823e5ab01940317c6ffc3a5fb69d8852b1842ff64f467baa8f0f502R83-R119

Changes are licensed under the European Union Public License 1.2 Copyright (c) StockerMC

The following class is licensed under the following license:

MIT License

Copyright (c) 2021 Devon (Gorialis) R

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

class ReactionProcedureTimer:
    """
    Class that reacts to a message based on what happens during its lifetime.
    """

    def __init__(self, timeout: float, ctx: Context):
        self.timeout = timeout
        self.ctx = ctx
        self.handle = None
        self.reacted = False

    async def __aenter__(self):
        self.handle = asyncio.create_task(self.react_after_sleep())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.handle:
            self.handle.cancel()

        if exc_val: # there was an exception
            await try_add_reaction(self.ctx.message, self.ctx.bot.error_emoji)
            return

        if self.reacted: # if there was a reaction
            await try_add_reaction(self.ctx.message, self.ctx.bot.success_emoji)

    async def react_after_sleep(self):
        await asyncio.sleep(self.timeout)
        self.reacted = await try_add_reaction(self.ctx.message, self.ctx.bot.arrow_emoji)

# The inspiration for how to make a decorator for a command was from
# https://github.com/EmoteBot/EmoteManager/blob/b0a3913391133b39ba159ede1c89054fac7fcaa3/cogs/emote.py#L238-L241
# https://github.com/EmoteBot/EmoteManager/blob/b0a3913391133b39ba159ede1c89054fac7fcaa3/utils/converter.py#L25-L38

def reactiontimer(command):
    """React to the command message with the bot's arrow emoji if the command takes 1 second or longer"""

    old_callback = command.callback

    @functools.wraps(old_callback)
    async def callback(self, ctx: Context, *args, **kwargs):
        async with ReactionProcedureTimer(2, ctx): # NOTE: make 3 instead of 2?
            return await old_callback(self, ctx, *args, **kwargs)

    # if we didn't do this, we would get a NameError for (some) command typehints
    callback.__globals__.update(old_callback.__globals__)

    command.callback = callback
    return command

# tests

@executor
def foo(a: int, *, b: str) -> bytes:
    return b""

# reveal_type(foo)

from discord.ext import commands

@reactiontimer # this has to be before the command decorator
@commands.command()
async def command(self, ctx: commands.Context, a: str, b: int, *, c: Optional[int] = 3):
    ...

# reveal_type(command)
