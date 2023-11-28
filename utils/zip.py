# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from __future__ import annotations

from zipfile import ZipFile, BadZipFile
import io
from discord.ext import commands
from .decorators import executor
from .emoji import PartialEmoji_
import collections
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from discord import Emoji

# credit to https://github.com/ioistired for this code
def clean_items(original: list[str]) -> list[str]:
    out = []
    counts = collections.Counter()
    for item in original:
        count = counts[item]
        if count != 0:
            out.append(f"{item}_{count}")
        else:
            out.append(item)
            
        counts[item] += 1

    return out

def filter_filenames(filenames: list[str]) -> list[str]:
    return [name for name in filenames if name.endswith((".pngs", ".jpg", ".jpeg", ".gif"))]

@executor
def create_zip_file(emojis: list[PartialEmoji_]) -> io.BytesIO:
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as f:
        for emoji in emojis:
            if TYPE_CHECKING:
                assert emoji.image is not None

            f.writestr(f"{emoji.name}.{'gif' if emoji.animated else 'png'}", emoji.image)

    buffer.seek(0)
    return buffer

async def zip_emojis(emojis: list[Emoji]) -> io.BytesIO:
    names = clean_items([emoji.name for emoji in emojis])
    buffer = await create_zip_file([PartialEmoji_(name, emoji.animated, image=await emoji.url.read()) for emoji, name in zip(emojis, names)])
    return buffer

@executor
def unzip_file(file_bytes: bytes) -> list[PartialEmoji_]:
    buffer = io.BytesIO(file_bytes)
    zip_file = ZipFile(buffer, "r")
    names = filter_filenames(zip_file.namelist())

    if not names:
        raise BadZipFile 

    emojis = []
    with zip_file as f:
        for name in names:
            image = f.read(name)
            name = name[:-4]
            animated = name.endswith(".gif")
            emojis.append(PartialEmoji_(name, animated, image=image))

    return emojis
