import asyncio
import edge_tts
import os
from config.settings import VOICES

class VoiceAgent:
    def __init__(self):
        pass

    async def _generate(self, text: str, voice: str, output_path: str):
        import random
        # Voice Diversity: Randomly adjust pitch and rate to create "unique" personas
        rates = ["+0%", "+5%", "+10%", "-5%", "-10%"]
        pitches = ["+0Hz", "+5Hz", "+10Hz", "-5Hz", "-10Hz"]
        rate = random.choice(rates)
        pitch = random.choice(pitches)
        
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
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
