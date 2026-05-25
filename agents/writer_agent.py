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
        
        CRITICAL INSTRUCTION: If the TOPIC/INSPIRATION is a "VIRAL YOUTUBE CONCEPT" (e.g. a title of a highly viewed video like 'Şekerin Zararları' or 'Unsolved Mysteries'), DO NOT just copy it. Instead, extract the CORE IDEA that made it viral.
        
        HOOK A/B TESTING:
        As an expert YouTube marketer, silently brainstorm 3 totally different "Hooks" (the first 3 seconds of the script). Evaluate which of the 3 hooks will have the absolute highest Retention and CTR (Click-Through Rate) based on human psychology. Then, write the ENTIRE SCRIPT using ONLY that WINNING hook. Hook the viewer instantly!

        DIRECTOR QUALITY CONTROL:
        Before outputting, SILENTLY review your script as a tough Hollywood Director. Rate it out of 10 internally. If the pacing is slow or the visual prompts are boring, rewrite the script internally to be faster and more engaging.
        DO NOT OUTPUT YOUR REVIEW, THOUGHTS, OR ANY TEXT. YOUR ENTIRE RESPONSE MUST BE ONLY THE RAW JSON OBJECT.
        
        CRITICAL TTS RULE: The 'voiceover_text' MUST be plain, grammatically correct text. DO NOT use emojis. DO NOT use markdown like ** or *. DO NOT use sound effects like "şşş", "hmm", "ahaha", "woohoo" because the AI voice will mispronounce them or spell them out. Just use plain words.

        CRITICAL VISUAL PROMPT RULE:
        The AI image generator WILL BLEND characters if you put them in the same prompt. For example, if you write 'A child and a goat', the AI will generate a terrifying 'child with goat ears'. 
        TO FIX THIS: Your 'visual_prompt' MUST contain ONLY ONE main subject per scene. 
        - BAD: "A child talking to a goat in a forest"
        - GOOD: "A cute white goat standing in a forest" or "A happy child smiling in a forest"
        Focus on extreme simplicity and single subjects.

        You MUST respond ONLY with a valid JSON object. Do not use markdown code blocks like ```json, just raw JSON.
        Format:
        {{
            "title": "Catchy YouTube Title",
            "description": "Video description with hashtags",
            "tags": ["tag1", "tag2"],
            "scenes": [
                {{
                    "visual_prompt": "Describe ONLY ONE subject. Very simple. English.",
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
            raise Exception("Gemini API failed to generate script. Aborting production to prevent dummy video upload.")
