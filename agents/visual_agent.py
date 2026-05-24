import requests
import os
import urllib.parse
from config.settings import PIXABAY_API_KEY

class VisualAgent:
    def __init__(self):
        self.pixabay_key = PIXABAY_API_KEY

    def get_image(self, prompt: str, channel_type: str, index: int) -> str:
        """
        Fetches an image. If channel is kids, tries to generate an AI image via pollinations.ai (free, no key).
        Otherwise fetches from Pixabay.
        """
        os.makedirs("temp_assets", exist_ok=True)
        file_path = f"temp_assets/img_{index}.jpg"

        if channel_type == "kids":
            # Use pollinations.ai for free AI cartoon generation
            safe_prompt = urllib.parse.quote(f"cute cartoon style, kids story book illustration, {prompt}")
            url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    return file_path
            except Exception as e:
                print(f"AI Image generation failed: {e}")
                # Fallback to pixabay

        # Fallback / Facts channel: Use Pixabay
        try:
            url = f"https://pixabay.com/api/?key={self.pixabay_key}&q={urllib.parse.quote(prompt)}&image_type=photo&orientation=vertical&per_page=3"
            response = requests.get(url).json()
            if 'hits' in response and len(response['hits']) > 0:
                img_url = response['hits'][0]['largeImageURL']
                img_data = requests.get(img_url).content
                with open(file_path, 'wb') as f:
                    f.write(img_data)
                return file_path
        except Exception as e:
            print(f"Pixabay fetch failed: {e}")
            
        return None
