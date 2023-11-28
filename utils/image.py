# (c) StockerMC
# SPDX-License-Identifier: EUPL-1.2

from .errors import CantCompressImage, CantConvertImage
import io
import logging
from .decorators import executor
from typing import cast, Callable

try:
    from wand.image import Image
except:
    logging.warning("ImageMagick or Wand was not found. Image compression and conversion will not be available. To install it, see https://docs.wand-py.org/en/0.4.1/guide/install.html.")
    has_wand = False
else:
    has_wand = True

# use all caps for formats?
FORMATS: dict[bool, str] = {
    True: "gif",
    False: "png"
}

# def recursive_resize(image: "Image", animated: bool) -> bytes:
# 	# test if we can increase the size for both animated and non animated
# 	if animated:
# 		amount = 0.4
# 	else:
# 		amount = 0.8

# 	get_new_size = lambda size: tuple(int(x * amount) for x in size)
# 	buffer = io.BytesIO()

# 	size = image.size
# 	while True:
# 		new_size = cast(tuple[int, int], get_new_size(size))
# 		if max(new_size) < 32:
# 			raise CantCompressImage

# 		frames = []

# 		for frame in ImageSequence.Iterator(image):
# 			frames.append(frame.resize(new_size).copy())

# 		# image = image.resize(cast(tuple[int, int], new_size))
# 		# image.seek(0)
# 		image.save(buffer, format=FORMATS[animated], optimize=True, quality=95, append_images=frames)
# 		if len(buffer.getvalue()) / 1028 <= 256:
# 			break

# 		size = new_size

# 	buffer.seek(0)
# 	return buffer.getvalue()

# @executor
# def compress_image(image: bytes) -> bytes:
# 	size = len(image) / 1028
# 	if size <= 256:
# 		return image

# 	animated = image.startswith(b"GIF")
# 	with Image.open(io.BytesIO(image)) as img:
# 		image = recursive_resize(img, animated)

# 	return image

# @executor
# def compress_image(image: bytes) -> bytes:
# 	size = len(image) / 1028
# 	print(f"{size=}")
# 	if size < 256:
# 		return image

# 	buffer = io.BytesIO()

# 	animated: bool = image.startswith(b"GIF")
# 	if animated:
# 		formats = ("GIF",)
# 	else:
# 		formats = ("PNG", "JPEG")

# 	with Image.open(io.BytesIO(image), formats=cast(tuple[str], formats)) as img:
# 		if not animated:
# 			img.save(buffer, format="PNG", optimize=True, quality=95)
# 			if len(buffer.getvalue()) / 1028 > 256:
# 				continue
# 			else:
# 				break

# 	return buffer.getvalue()

# 	# with Image(blob=io.BytesIO(image), background="transparent") as img:
# 	# 	image_width = img.width
# 	# 	image_height = img.height
# 	# 	while size > 256:
# 	# 		if image_height < 32 or image_width < 32: # we don't want to resize smaller than 32 pixels, so raise
# 	# 			raise CantCompressImage

# 	# 		img.compression_quality = 75
# 	# 		image_width = int(image_width / 2)
# 	# 		image_height = int(image_height / 2)
# 	# 		img.resize(width=image_width, height=image_height)
# 	# 		img.save(file=buffer)
# 	# 		size = len(buffer.getvalue()) / 1028

# 	# return buffer.getvalue(), True

@executor
def convert_to_gif(image: bytes) -> bytes:
    buffer = io.BytesIO()
    # test if this works and is transparent
    with Image(blob=io.BytesIO(image), background="transparent", format="png") as img:
        img.save(buffer)

    return buffer.getvalue()

async def compress_image(a): return a # temp
