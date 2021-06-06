from zipfile import ZipFile
import io
import aiohttp

async def zip_emojis(emojis):
	zip_file = io.BytesIO()
	with ZipFile(zip_file, "w") as f:
		temp = {}
		for emoji in emojis:
			data = await emoji.url_as().read()
			try:
				f.writestr(f"{emoji.name}.{'gif' if emoji.animated else 'png'}", data)
			except UserWarning:
				n = temp.get(emoji.name)
				if n is None:
					temp[emoji.name] = 1
				else:
					temp[emoji.name] += 1
				f.writestr(f"{emoji.name}_{temp[emoji.name]}.{'gif' if emoji.animated else 'png'}", data)
	
	zip_file.seek(0)
	return zip_file

def unzip_file(file_bytes): 
	file = ZipFile(io.BytesIO(file_bytes), "r")
	names = [name for name in file.namelist() if name.endswith((".png", ".jpg", ".jpeg", ".gif"))]

	if not names:
		return None
	
	emojis = []

	with file as f:
		for name in names:
			image = f.read(name)
			data = {"image": image, "name": name[:-4], "animated": bool(name[-4:] == ".gif")}
			if data not in emojis:
				emojis.append(data)

	return emojis

async def fetch_zip_url(url, bot):
	#if not url.endswith(".zip"):
	#	return False
	timeout = aiohttp.ClientTimeout(total=60) # type: ignore
	async with bot.session.get(url, timeout=timeout) as response:
		assert response.status == 200
		zip_file = await response.read()
		return zip_file