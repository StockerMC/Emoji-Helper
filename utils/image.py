from PIL import Image
from .errors import CantCompressImage
import io

def compress_image(image_bytes):
	max_retries = 4 # or 5
	retries = 0
	kb_size = len(image_bytes) / 1000 # bytes / 1000 = kilobytes
	image = Image.open(io.BytesIO(image_bytes))

	try:
		image.seek(1)
	except EOFError:
		animated = False
	else:
		animated = True

	output = io.BytesIO()

	while kb_size > 256:
		if retries == max_retries: # or greater than?
			raise CantCompressImage("Exceeded max retries")
		new_size = tuple(int(v // 2.053) for v in image.size) # or just v / 1.25?
		print(new_size)
		if new_size[0] <= 0 or new_size[1] <= 0:
			raise CantCompressImage("Size can't be below 0")

		image = image.resize(new_size, Image.ANTIALIAS) # regularly antialias
		image.save(output, optimize=True, quality=95, format="GIF" if animated else "PNG")
		if len(output.getvalue()) / 1000 > kb_size:
			raise CantCompressImage("Image increasing in size")
		kb_size = len(output.getvalue()) / 1000
		print(kb_size)
		retries += 1

	return output.getvalue()

# filename = "the-capsule.png"

# import asyncio

# loop = asyncio.get_event_loop()

# async def compress_image_coro():
# 	with open(filename, "rb") as f:
# 		original_bytes = f.read()
# 		e = await loop.run_in_executor(None, compress_image, original_bytes)


# 	with open(filename, "wb") as f:
# 		f.write(e.getvalue())

# 	await asyncio.sleep(2.5)
# 	with open(filename, "wb") as f:
# 		f.write(original_bytes)

# loop.run_until_complete(compress_image_coro())