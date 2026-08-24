import requests
import os
import urllib.parse
import re
from PIL import Image
from config.settings import PIXABAY_API_KEY
from agents.safety_agent import SafetyAgent

# Comprehensive blacklist of words that could trigger NSFW, suggestive, or nude AI outputs
RISKY_KEYWORDS = [
    "nude", "naked", "nudity", "bare skin", "bare chest", "bikini", "lingerie", 
    "cleavage", "underwear", "undressed", "unclothed", "topless", "bottomless",
    "erotic", "sexy", "sensual", "flesh", "corpse", "nakedness", "bathing", "shower",
    "swimsuit", "provocative", "strip", "breast", "buttock", "penis", "vagina", "genital",
    "erotica", "scantily", "swimwear", "intimate"
]

class VisualAgent:
    def __init__(self):
        self.pixabay_key = PIXABAY_API_KEY
        self.safety_agent = SafetyAgent()

    def _sanitize_prompt(self, prompt: str) -> str:
        """
        Scans and sanitizes the prompt against risky or NSFW keywords.
        Replaces flagged descriptions with 100% safe, atmospheric documentary visual concepts.
        """
        lower_prompt = prompt.lower()
        for word in RISKY_KEYWORDS:
            if re.search(r'\b' + re.escape(word) + r'\b', lower_prompt):
                print(f"[Visual Agent] [SAFETY FILTER] Filtered risky keyword '{word}' from visual prompt! Replacing with safe concept.")
                return "Mysterious vintage classified dossier file on a dark wooden table in a dimly lit archival library, dark cinematic, 8k resolution"
        return prompt

    def get_image(self, prompt: str, channel_type: str, index: int, visual_style: str = "cinematic") -> str:
        """
        Fetches an image or video with strict multi-layer NSFW and safety filters.
        1. Sanitizes prompt against risky keywords.
        2. Tries Pixabay with SafeSearch enabled, or Pollinations AI with SFW enforcement.
        3. Passes all media through Gemini Vision automated moderation before approval.
        4. Provides guaranteed safe fallback visual if generation or check fails.
        """
        os.makedirs("temp_assets", exist_ok=True)
        file_path = f"temp_assets/img_{index}.jpg"

        # Step 1: Sanitize prompt
        clean_prompt = self._sanitize_prompt(prompt)

        # Step 2: Mandatory safety prompt prefix
        safety_prefix = "family safe, strictly safe for work, fully clothed, modest attire, no nudity, no bare skin, professional documentary"

        if channel_type == "kids":
            enhanced_prompt = f"Cute 3D Pixar Disney animation style, extremely cute, child-friendly, colorful, bright, safe for kids, fully clothed, {clean_prompt}"
        else:
            enhanced_prompt = f"{visual_style} style, masterpiece, best quality, cinematic lighting, {safety_prefix}, {clean_prompt}"
            
        safe_prompt = urllib.parse.quote(enhanced_prompt)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true&model=flux&safe=true"

        def create_safe_fallback() -> str:
            """Generates a 100% safe, verified scenic/space fallback visual."""
            fallback_path = f"temp_assets/safe_fallback_{index}.jpg"
            safe_query = urllib.parse.quote("Deep space cosmic nebula stars galaxies dark cinematic 8k wallpaper")
            safe_url = f"https://image.pollinations.ai/prompt/{safe_query}?width=1080&height=1920&nologo=true&safe=true"
            try:
                res = requests.get(safe_url, timeout=30)
                if res.status_code == 200:
                    with open(fallback_path, 'wb') as f:
                        f.write(res.content)
                    return fallback_path
            except Exception:
                pass

            # Offline solid-state fallback
            Image.new('RGB', (1080, 1920), color=(15, 23, 42)).save(fallback_path)
            return fallback_path

        # Step 3: Try Pixabay VIDEO with Strict SafeSearch for non-kids channels
        if channel_type != "kids" and self.pixabay_key and self.pixabay_key != "yok":
            try:
                # Sanitize search term to landscape / nature / mystery
                clean_query = urllib.parse.quote(clean_prompt[:40] + " cinematic mystery")
                pixabay_url = f"https://pixabay.com/api/videos/?key={self.pixabay_key}&q={clean_query}&video_type=all&safesearch=true&per_page=5"
                response = requests.get(pixabay_url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if 'hits' in data and len(data['hits']) > 0:
                        best_vid = data['hits'][0]
                        for hit in data['hits']:
                            if hit.get('videos', {}).get('large', {}).get('url'):
                                best_vid = hit
                                break
                        
                        vid_url = best_vid['videos']['large']['url']
                        vid_data = requests.get(vid_url, timeout=30).content
                        vid_path = f"temp_assets/vid_{index}.mp4"
                        with open(vid_path, 'wb') as f:
                            f.write(vid_data)

                        # Moderation check on video
                        if self.safety_agent.is_media_safe(vid_path):
                            return vid_path
                        else:
                            print(f"[Visual Agent] [WARNING] Pixabay video rejected by safety agent. Falling back to AI...")
            except Exception as e:
                print(f"[Visual Agent] Pixabay video fetch failed: {e}. Falling back to AI...")

        # Step 4: Try Pollinations AI with Safe Mode and Moderation
        import time
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=40)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)

                    # Moderation check on AI image
                    if self.safety_agent.is_media_safe(file_path):
                        return file_path
                    else:
                        print(f"[Visual Agent] [ALERT] Generated image FAILED safety check (attempt {attempt+1}). Replacing with safe fallback...")
                        return create_safe_fallback()
            except Exception as e:
                print(f"[Visual Agent] Pollinations AI failed (attempt {attempt+1}): {e}")
            time.sleep(2)

        # Step 5: If all attempts fail, return safe fallback
        print("[Visual Agent] Returning guaranteed safe fallback image.")
        return create_safe_fallback()
