"""
Changes are licensed under the European Union Public License 1.2 Copyright (c) StockerMC

The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import aiohttp
import asyncio
import discord
from discord.http import HTTPClient, Route, json_or_text, MaybeUnlock
from discord import __version__, utils
from discord.errors import HTTPException, Forbidden, NotFound, DiscordServerError
from .errors import RateLimited
from urllib.parse import quote as _uriquote
import logging
import time
from typing import TYPE_CHECKING

log = logging.getLogger('discord')

# Route.BASE = "https://discord.com/api/v9"

class EmojiHTTPClient(HTTPClient):
    """Unlike HTTPClient, when a request returns with a 429 status code, RateLimited is raised instead of sleeping""" # edit this?

    def __init__(self, token: str, session: aiohttp.ClientSession):
        super().__init__()
        self.token = token
        self.__session = session
        self.rate_limits: dict[int, dict[str, float]] = {}
        self.requests: dict[str, int] = {}

    def set_rate_limit(self, guild_id: int, method: str, retry_after: int):
        try:
            rate_limits = self.rate_limits[guild_id]
        except KeyError:
            rate_limits = self.rate_limits[guild_id] = {}

        rate_limits[method] = time.time() + retry_after

    async def request(self, route: Route, *, files=None, form=None, **kwargs):
        bucket = route.bucket
        method = route.method
        url = route.url

        if TYPE_CHECKING:
            assert route.guild_id is not None # lazy type guarding

        rate_limits = self.rate_limits.get(route.guild_id)
        if rate_limits:
            rate_limit_time = rate_limits.get(route.method)
            if rate_limit_time is not None:
                if time.time() > rate_limit_time:
                    del rate_limits[route.method]
                else:
                    raise RateLimited(rate_limit_time)

        lock = self._locks.get(bucket)
        if lock is None:
            lock = asyncio.Lock()
            if bucket is not None:
                self._locks[bucket] = lock

        # header creation
        headers = {
            'User-Agent': self.user_agent,
            'Authorization': f'Bot {self.token}'
        }

        # some checking if it's a JSON request
        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = utils.to_json(kwargs.pop('json'))

        try:
            reason = kwargs.pop('reason')
        except KeyError:
            pass
        else:
            if reason:
                headers['X-Audit-Log-Reason'] = _uriquote(reason, safe='/ ')

        kwargs['headers'] = headers

        # Proxy support
        if self.proxy is not None:
            kwargs['proxy'] = self.proxy
        if self.proxy_auth is not None:
            kwargs['proxy_auth'] = self.proxy_auth

        if not self._global_over.is_set():
            # wait until the global lock is complete
            await self._global_over.wait()

        await lock.acquire()
        with MaybeUnlock(lock) as maybe_lock:
            for tries in range(5):
                if files:
                    for f in files:
                        f.reset(seek=tries)

                if form:
                    form_data = aiohttp.FormData()
                    for params in form:
                        form_data.add_field(**params)
                    kwargs['data'] = form_data

                try:
                    async with self.__session.request(method, url, **kwargs) as r:
                        try: # remove this 
                            self.requests[method] += 0
                        except KeyError:
                            self.requests[method] = 1
                        
                        log.debug('%s %s with %s has returned %s', method, url, kwargs.get('data'), r.status)

                        # even errors have text involved in them so this is safe to call
                        data = await json_or_text(r)

                        # check if we have rate limit header information
                        remaining = r.headers.get('X-Ratelimit-Remaining')
                        if remaining == '0' and r.status != 429:
                            # we've depleted our current bucket
                            delta = utils._parse_ratelimit_header(r, use_clock=self.use_clock)
                            log.debug('A rate limit bucket has been exhausted (bucket: %s, retry: %s).', bucket, delta)
                            maybe_lock.defer()
                            self.loop.call_later(delta, lock.release)

                        # the request was successful so just return the text/json
                        if 300 > r.status >= 200:
                            log.debug('%s %s has received %s', method, url, data)
                            return data

                        # we are being rate limited
                        if r.status == 429:
                            if not r.headers.get('Via'):
                                # Banned by Cloudflare more than likely.
                                raise HTTPException(r, data)


                            retry_after = data['retry_after'] / 1000.0 # type: ignore

                            # check if it's a global rate limit
                            is_global = data.get('global', False) # type: ignore
                            if is_global:
                                log.warning('Global rate limit has been hit. Retrying in %.2f seconds.', retry_after)
                                self._global_over.clear()

                                await asyncio.sleep(retry_after)
                                log.debug('Done sleeping for the global rate limit. Retrying...')
                            else:
                                fmt = 'We are being rate limited. Retrying in %.2f seconds. Handled under the bucket "%s"'
                                log.warning(fmt, retry_after, bucket)
                                if retry_after > 10000:
                                    self.set_rate_limit(route.guild_id, route.method, retry_after) # type: ignore
                                    raise RateLimited(retry_after)
                                else:
                                    await asyncio.sleep(retry_after)
                                    continue

                            # release the global lock now that the
                            # global rate limit has passed
                            if is_global:
                                self._global_over.set()
                                log.debug('Global rate limit is now over.')

                            continue

                        # we've received a 500 or 502, unconditional retry
                        if r.status in {500, 502}:
                            await asyncio.sleep(1 + tries * 2)
                            continue

                        # the usual error cases
                        if r.status == 403:
                            raise Forbidden(r, data)
                        elif r.status == 404:
                            raise NotFound(r, data)
                        elif r.status == 503:
                            raise DiscordServerError(r, data)
                        else:
                            raise HTTPException(r, data)

                # This is handling exceptions from the request
                except OSError as e:
                    # Connection reset by peer
                    if tries < 4 and e.errno in (54, 10054):
                        continue
                    raise

            # We've run out of retries, raise.
            if r.status >= 500: # type: ignore
                raise DiscordServerError(r, data) # type: ignore

            raise HTTPException(r, data) # type: ignore

    async def create_custom_emoji(self, guild: discord.Guild, *, name: str, image: bytes, roles: list[int] = None, reason: str = None):
        payload = {
            'name': name,
            'image': utils._bytes_to_base64_data(image),
            'roles': roles or []
        }

        r = Route('POST', '/guilds/{guild_id}/emojis', guild_id=guild.id)
        data = await self.request(r, json=payload, reason=reason)
        return guild._state.store_emoji(guild, data)
