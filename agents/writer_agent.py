import google.generativeai as genai
import json
from config.settings import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

class WriterAgent:
    def __init__(self):
        # We use gemini-2.5-flash as it's fast and free tier is generous
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def write_script(self, topic: str, channel_type: str, language: str, format_type: str) -> dict:
        """
        Uses Gemini to generate a video script in JSON format.
        """
        duration = "45 seconds" if format_type == "shorts" else "3 minutes"
        
        prompt = f"""
        Write a video script for a YouTube {format_type}.
        Channel type: {channel_type} (kids cartoon/story OR adult facts/history).
        Language: {language.upper()}
        Approximate duration: {duration}

        TOPIC/INSPIRATION: {topic}
        
        CRITICAL INSTRUCTION: If the TOPIC/INSPIRATION is a "VIRAL YOUTUBE CONCEPT" (e.g. a title of a highly viewed video like 'Şekerin Zararları' or 'Unsolved Mysteries'), DO NOT just copy it. Instead, extract the CORE IDEA that made it viral, and write a COMPLETELY ORIGINAL, unique, and engaging script based on that same viral core idea. Hook the viewer in the first 3 seconds!


        You MUST respond ONLY with a valid JSON object. Do not use markdown code blocks like ```json, just raw JSON.
        Format:
        {{
            "title": "Catchy YouTube Title",
            "description": "Video description with hashtags",
            "tags": ["tag1", "tag2"],
            "scenes": [
                {{
                    "visual_prompt": "Describe what image to search or generate for this scene",
                    "voiceover_text": "The exact text to be spoken by the narrator"
                }},
                ...
            ]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            # Clean up potential markdown formatting
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            print(f"Error generating script: {e}")
            # Fallback script
            return {
                "title": "Amazing Video",
                "description": "Check this out! #shorts",
                "tags": ["video"],
                "scenes": [
                    {
                        "visual_prompt": "nature landscape",
                        "voiceover_text": "Welcome to an amazing new video." if language == "en" else "Harika bir videoya hoş geldiniz."
                    }
                ]
            }
