import asyncio
import edge_tts
import os
from config.settings import VOICES

class VoiceAgent:
    def __init__(self):
        pass

    async def _generate(self, text: str, voice: str, output_path: str):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    def generate_voiceover(self, text: str, channel_type: str, language: str, output_path: str):
        """
        Generates TTS audio and saves it to output_path.
        """
        voice_key = "kids_narrator" if channel_type == "kids" else "facts_narrator"
        voice = VOICES[language][voice_key]
        
        asyncio.run(self._generate(text, voice, output_path))
        return output_path
