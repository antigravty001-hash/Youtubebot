import google.generativeai as genai
import json
from config.settings import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

class WriterAgent:
    def __init__(self):
        # We will try to find a model that has free quota and doesn't return 404/429
        self.models_to_try = [
            'gemini-1.5-flash-8b',  # Very fast, huge free tier
            'gemini-1.5-flash',     # 1500 free requests per day
            'gemini-1.0-pro',       # Legacy stable, high free tier
            'gemini-pro',           # Older alias for 1.0 pro
            'gemini-2.0-flash'      # Works, but has 20 req/day limit (fallback of last resort)
        ]
        self.model = None

    def _get_working_model(self):
        """Finds and returns the first working Gemini model"""
        for model_name in self.models_to_try:
            try:
                print(f"[Writer Agent] Trying model: {model_name}...")
                model = genai.GenerativeModel(model_name)
                # Quick test
                model.generate_content("test")
                print(f"[Writer Agent] Successfully connected to {model_name}!")
                return model
            except Exception as e:
                print(f"[Writer Agent] Model {model_name} failed: {e}")
                continue
        raise Exception("All Gemini models failed. Check API key quotas.")

    def write_script(self, topic: str, channel_type: str, language: str, format_type: str) -> dict:
        """
        Generates a viral script using Gemini.
        """
        if not self.model:
            self.model = self._get_working_model()
        if format_type == "shorts":
            duration_instruction = "Approximate duration: 45 seconds. CRITICAL RULE: Your ENTIRE script (voiceover_text combined) MUST NOT exceed 100 words! If it is longer, YouTube will reject it as a Short."
        else:
            duration_instruction = "Approximate duration: 3 minutes. CRITICAL RULE: Aim for around 400-500 words for the voiceover."
            
        prompt = f"""
        You are a master scriptwriter for a dark, eerie, Netflix-style documentary channel called 'Unknown Archives'.
        Write a video script for a YouTube {format_type}.
        Language: {language.upper()}
        {duration_instruction}

        TOPIC/INSPIRATION: {topic}
        
        CRITICAL SCRIPTING RULES:
        1. HOOK: Start with an extreme, unsettling hook that immediately grabs attention. (e.g., "The universe is hiding a terrifying secret," or "What you are about to hear will change how you sleep.")
        2. TONE: Dark, mysterious, serious, and deeply engaging. 
        3. CALL TO ACTION: End the script with a compelling, thematic subscribe call (e.g., "Karanlık sırların devamı için arşive katıl" or "Subscribe to uncover more unknown archives.")
        
        CRITICAL TTS RULE: The 'voiceover_text' MUST be plain, grammatically correct text. DO NOT use emojis. DO NOT use sound effects like "şşş", "hmm". Just use plain words.

        CRITICAL VISUAL PROMPT RULE (HYPER-REALISM):
        The AI image generator must create stunning, terrifying, and awe-inspiring images. You CANNOT use simple prompts like "Space" or "A star".
        Your 'visual_prompt' MUST be highly descriptive, English only, and MUST include these style keywords: 
        ", dark cinematic, hyper-realistic, 8k resolution, Unreal Engine 5 render, highly detailed, atmospheric lighting, masterpiece, documentary footage"
        
        Example Good Visual Prompt: "A massive, terrifying black hole consuming a dying star, dark cinematic, hyper-realistic, 8k resolution, Unreal Engine 5 render, highly detailed, atmospheric lighting, masterpiece"
        
        You MUST respond ONLY with a valid JSON object. Do not use markdown code blocks like ```json.
        Format:
        {{
            "title": "Catchy, Eerie YouTube Title",
            "description": "Video description with hashtags",
            "tags": ["mystery", "space", "scary", "facts", "unknown"],
            "scenes": [
                {{
                    "visual_prompt": "Highly detailed English prompt with 8K UE5 keywords",
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
