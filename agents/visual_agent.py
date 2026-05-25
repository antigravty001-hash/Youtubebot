import requests
import os
import urllib.parse
from config.settings import PIXABAY_API_KEY

class VisualAgent:
    def __init__(self):
        self.pixabay_key = PIXABAY_API_KEY

    def get_image(self, prompt: str, channel_type: str, index: int, visual_style: str = "cinematic") -> str:
        """
        Fetches an image. Tries Pixabay for facts, but falls back to Pollinations AI for everything if it fails.
        """
        os.makedirs("temp_assets", exist_ok=True)
        file_path = f"temp_assets/img_{index}.jpg"

        def use_pollinations():
            enhanced_prompt = f"{visual_style} style, masterpiece, best quality, perfect anatomy, highly detailed, {prompt}"
            safe_prompt = urllib.parse.quote(enhanced_prompt)
            # Added model=flux and enhance=true for world-class anatomy and realism
            url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true&model=flux&enhance=true"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    return file_path
            except Exception as e:
                print(f"Pollinations AI failed: {e}")
            return None

        if channel_type == "kids" or not self.pixabay_key or self.pixabay_key == "yok":
            return use_pollinations()

        # Try Pixabay VIDEO for Facts channel
        try:
            url = f"https://pixabay.com/api/videos/?key={self.pixabay_key}&q={urllib.parse.quote(prompt)}&video_type=all&per_page=3"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if 'hits' in data and len(data['hits']) > 0:
                    # Find a vertical video if possible, else just use the best HD one
                    best_vid = data['hits'][0]
                    for hit in data['hits']:
                        # Prefer vertical or HD videos
                        if hit['videos']['large']['url']:
                            best_vid = hit
                            break
                    
                    vid_url = best_vid['videos']['large']['url']
                    vid_data = requests.get(vid_url).content
                    vid_path = f"temp_assets/vid_{index}.mp4"
                    with open(vid_path, 'wb') as f:
                        f.write(vid_data)
                    return vid_path
        except Exception as e:
            print(f"Pixabay video fetch failed: {e}. Falling back to AI...")
            
        # Fallback if Pixabay fails
        return use_pollinations()
