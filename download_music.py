import urllib.request
import os

urls = [
    ("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", "track1.mp3"),
    ("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3", "track2.mp3")
]

os.makedirs("bgm", exist_ok=True)
for url, filename in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(f"bgm/{filename}", 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print(f"Downloaded {filename}")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")
