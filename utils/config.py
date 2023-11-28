# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from __future__ import annotations

import toml
import discord
from collections.abc import Mapping, Iterator
from typing import TYPE_CHECKING, Union, Any

if TYPE_CHECKING:
    from os import PathLike

class ConfigNamespace(Mapping[str, Any]):
    def __init__(self, data: Mapping[str, Any]):
        self.__dict__.update(data)

    """
    https://github.com/GenericDiscordBot/Generic-Bot/commit/f002e9894765dd9cd989c72ad947e43c3bf58271#diff-2285afabac772ea4b972efbefe6b84146db7671d567afb2204f7e3e2f3ae7e1bR8-R21

    The below functions in this class are licensed under the following license:

    MIT License

    Copyright (c) 2021 Zomatree

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

    def __iter__(self) -> Iterator[str]:
        yield from self.__dict__.keys()

    def __getitem__(self, key: str) -> Any:
        return self.__dict__[key]

    def __len__(self) -> int:
        return len(self.__dict__)

    def __getattr__(self, key: str) -> Any:
        try:
            return super().__getattribute__(key)
        except AttributeError:
            try:
                return self.__dict__[key]
            except KeyError:
                raise AttributeError(key)

class Config(ConfigNamespace):
    def __init__(self, filename: Union[str, PathLike]):
        config = toml.load(filename)

        self.bot = ConfigNamespace(config["bot"])
        self.prefix = ConfigNamespace(config["prefix"])
        self.emojis = ConfigNamespace(config["emojis"])
        self.database = ConfigNamespace(config["database"])
        self.jishaku = ConfigNamespace(config["jishaku"])
        self.logging = ConfigNamespace(config["logging"])
        self.channels = ConfigNamespace(config["channels"])
        self.license = ConfigNamespace(config["license"])

        # type checking

        if type(self.bot.color) not in (str, int):
            raise TypeError("[bot].color should be a string or an int")

        if type(self.bot.case_sensitive) is not bool:
            raise TypeError("[bot].case_sensitive should be a bool")

        if type(self.prefix.mentionable) is not bool:
            raise TypeError("[prefix].mentionable should be a bool")

        if type(self.database.use_database) is not bool:
            raise TypeError("[prefix].mentionable should be a bool")

        if type(self.logging.print) is not bool:
            raise TypeError("[bot].case_sensitive should be a bool")

        for k, v in self.channels.items():
            if v and type(v) is not int:
                raise ValueError(f"[channels].{k} should be an int")
