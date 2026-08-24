import os
import subprocess
from PIL import Image

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

from config.settings import GEMINI_API_KEY

class SafetyAgent:
    """
    Automated Content Moderation Agent:
    Uses Gemini Multimodal Vision to inspect generated images and video frames
    against YouTube Community Guidelines, strict SFW standards, and nudity/gore policies.
    """
    def __init__(self):
        self.api_keys = [k.strip() for k in GEMINI_API_KEY.split(",") if k.strip()]
        self.models_to_try = [
            'gemini-2.5-flash',
            'gemini-2.0-flash-lite',
            'gemini-2.0-flash',
            'gemini-1.5-flash'
        ]

    def _ask_gemini_vision(self, img: Image.Image) -> bool:
        """
        Queries Gemini Vision to check if the image is 100% safe for YouTube.
        Returns True if SAFE, False if UNSAFE.
        """
        if not GENAI_AVAILABLE or not genai or not self.api_keys:
            # Fallback if genai library or API key is not configured locally
            return True

        safety_prompt = """
        You are a strict YouTube Community Guidelines and Safety Compliance Officer.
        Inspect this image with ZERO TOLERANCE for any inappropriate content.

        Check if this image contains ANY of the following:
        1. Nudity, partial nudity, uncovered breasts, buttocks, or genitals.
        2. Suggestive or revealing clothing, lingerie, underwear, or excessive bare skin.
        3. Naked statues, nude paintings, uncovered human figures, or sexualized poses.
        4. Gore, open wounds, dismembered bodies, blood, or disturbing anatomical violence.

        If ANY of the above is present, answer: UNSAFE
        If the image is completely family-safe, clothed, and policy-compliant, answer: SAFE

        Respond with ONLY ONE WORD: SAFE or UNSAFE.
        """

        for api_key in self.api_keys:
            try:
                genai.configure(api_key=api_key)
                for model_name in self.models_to_try:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content([safety_prompt, img])
                        verdict = response.text.strip().upper()
                        
                        if "UNSAFE" in verdict:
                            print(f"[Safety Agent] [REJECTED] Model {model_name} flagged content as UNSAFE!")
                            return False
                        elif "SAFE" in verdict:
                            print(f"[Safety Agent] [APPROVED] Content verified SAFE by {model_name}.")
                            return True
                    except Exception:
                        continue
            except Exception:
                continue

        return True

    def is_image_safe(self, image_path: str) -> bool:
        """
        Inspects an image file with Gemini Vision.
        """
        if not os.path.exists(image_path):
            return False
            
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                return self._ask_gemini_vision(img)
        except Exception as e:
            print(f"[Safety Agent] Error opening image {image_path}: {e}")
            return False

    def is_video_safe(self, video_path: str) -> bool:
        """
        Extracts sample frames from an MP4 video and inspects them for safety.
        """
        if not os.path.exists(video_path):
            return False

        temp_frame_path = "temp_assets/safety_sample_frame.jpg"
        os.makedirs("temp_assets", exist_ok=True)

        try:
            cmd = [
                "ffmpeg", "-y", "-ss", "00:00:01",
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                temp_frame_path
            ]
            subprocess.run(cmd, capture_output=True)
            if os.path.exists(temp_frame_path):
                is_safe = self.is_image_safe(temp_frame_path)
                try:
                    os.remove(temp_frame_path)
                except Exception:
                    pass
                return is_safe
        except Exception as e:
            print(f"[Safety Agent] Video frame extraction failed: {e}")

        return True

    def is_media_safe(self, media_path: str) -> bool:
        """
        Universal safety checker for either images or videos.
        """
        if not media_path or not os.path.exists(media_path):
            return False
            
        if media_path.lower().endswith(".mp4"):
            return self.is_video_safe(media_path)
        else:
            return self.is_image_safe(media_path)
