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

    def generate_voiceover(self, text: str, voice_gender: str, language: str, output_path: str):
        """
        Generates TTS audio and saves it to output_path.
        """
        # default to female if invalid
        gender = voice_gender if voice_gender in ["female", "male"] else "female"
        voice = VOICES[language][gender]
        
        asyncio.run(self._generate(text, voice, output_path))
        return output_path
