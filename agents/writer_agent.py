import google.generativeai as genai
import json
import random
from config.settings import GEMINI_API_KEY

class WriterAgent:
    def __init__(self):
        self.models_to_try = [
            'gemini-2.5-flash',     # Works for user, 20/day limit per key
            'gemini-2.0-flash-lite',
            'gemini-1.5-flash-002',
            'gemini-1.5-flash',
            'gemini-1.0-pro',
            'gemini-pro',
            'gemini-2.0-flash'
        ]
        
        # Support multiple API keys separated by comma
        self.api_keys = [k.strip() for k in GEMINI_API_KEY.split(",") if k.strip()]
        self.model = None

    def _get_working_model(self):
        """Finds and returns the first working Gemini model using multiple API keys"""
        # Shuffle keys to distribute load if multiple are provided
        keys_to_try = list(self.api_keys)
        random.shuffle(keys_to_try)
        
        for api_key in keys_to_try:
            print(f"[Writer Agent] Trying API Key: {api_key[:8]}...{api_key[-4:]}")
            genai.configure(api_key=api_key)
            
            for model_name in self.models_to_try:
                try:
                    print(f"  -> Testing model: {model_name}...")
                    model = genai.GenerativeModel(model_name)
                    # Quick test
                    model.generate_content("test")
                    print(f"[Writer Agent] 🟢 Successfully connected to {model_name} with this key!")
                    return model
                except Exception as e:
                    print(f"  -> Model {model_name} failed: {e}")
                    continue
                    
        raise Exception("All Gemini models on ALL API keys failed. Check API key quotas or add more keys.")

    def write_script(self, topic: str, channel_type: str, language: str, format_type: str) -> dict:
        """
        Generates a viral script using Gemini.
        """
        if not self.model:
            self.model = self._get_working_model()
        if format_type == "shorts":
            duration_instruction = "Approximate duration: 55 seconds. CRITICAL RULE: Your ENTIRE script (voiceover_text combined) MUST be exactly 130 to 150 words long to ensure the video is exactly 50-60 seconds long!"
        else:
            duration_instruction = "Approximate duration: 3 minutes. CRITICAL RULE: Aim for around 400-500 words for the voiceover."
            
        prompt = f"""
        You are a master scriptwriter for a dark, eerie, Netflix-style documentary channel called 'Unknown Archives'.
        Write a video script for a YouTube {format_type}.
        Language: {language.upper()}
        {duration_instruction}

        TOPIC/INSPIRATION: {topic}
        
        ═══════════════════════════════════════════
        OUROBOROS LOOP RULE (MOST CRITICAL - READ CAREFULLY):
        ═══════════════════════════════════════════
        Your script MUST form a PERFECT INFINITE LOOP. The viewer must NOT realize the video has restarted.
        
        HOW: The LAST scene's voiceover_text must END with an INCOMPLETE sentence or cliffhanger 
        that GRAMMATICALLY and LOGICALLY continues into the FIRST scene's voiceover_text (the hook).
        
        Example (TR):
        - Last scene ends with: "...ve bu sırrı dünyadan saklamanın asıl nedeni..."
        - First scene (hook) starts with: "...insanlığın henüz hazır olmadığı bir gerçeği barındırmasıydı."
        
        Example (EN):
        - Last scene ends with: "...and the real reason they buried this secret was..."
        - First scene (hook) starts with: "...because what they found would shatter everything we believe."
        
        The transition must be SEAMLESS. No "subscribe" or CTA at the very end. Instead, place any 
        subscribe call in the SECOND TO LAST scene, so the final scene is purely the loop cliffhanger.
        ═══════════════════════════════════════════

        CRITICAL SCRIPTING RULES:
        1. HOOK: Start with the second half of the loop sentence, then immediately hit with an extreme, unsettling hook.
        2. FACTS: You MUST include exactly 3 to 4 distinct, mind-blowing, highly secretive hidden facts. Frame them as 'Top Secret', 'Highly Classified', or 'Knowledge they tried to hide from you'. Do NOT just give general information.
        3. TONE: Dark, mysterious, serious, and deeply engaging. It must feel like exposing a grand conspiracy.
        4. SUBSCRIBE CTA: Place a compelling subscribe call in the SECOND TO LAST scene (NOT the last scene).
        5. LOOP ENDING: The LAST scene must end with an unfinished sentence that feeds back into the first scene's hook.
        
        SUBTLE ENGAGEMENT EASTER EGG:
        In exactly ONE of the scenes' visual_prompt, hide a VERY subtle anachronism that only eagle-eyed 
        viewers would notice (e.g., a barely visible modern object in a historical setting, or a shadow 
        that doesn't match). This must be EXTREMELY subtle — do NOT mention it in the voiceover. 
        It is a secret visual detail for curious viewers who will comment about it.
        
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
