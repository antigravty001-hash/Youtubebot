import asyncio
import edge_tts
import os
from config.settings import VOICES

class VoiceAgent:
    def __init__(self):
        pass

    async def _generate(self, text: str, voice: str, output_path: str):
        import random
        rates = ["+0%", "+5%", "+10%", "-5%", "-10%"]
        pitches = ["+0Hz", "+5Hz", "+10Hz", "-5Hz", "-10Hz"]
        rate = random.choice(rates)
        pitch = random.choice(pitches)
        
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        
        # We will manually collect word boundaries to create 3-word chunks for subtitles
        word_boundaries = []
        
        with open(output_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    word_boundaries.append(chunk)

        # Generate SRT
        def format_time(t_100ns):
            s = t_100ns / 10_000_000
            h = int(s / 3600)
            m = int((s % 3600) / 60)
            sec = int(s % 60)
            ms = int((s - int(s)) * 1000)
            return f"{h:02}:{m:02}:{sec:02},{ms:03}"

        srt_path = output_path.replace(".mp3", ".srt")
        srt_content = ""
        chunk_size = 3
        counter = 1
        
        for i in range(0, len(word_boundaries), chunk_size):
            chunk_words = word_boundaries[i:i+chunk_size]
            if not chunk_words: continue
            
            start_t = chunk_words[0]["offset"]
            end_t = chunk_words[-1]["offset"] + chunk_words[-1]["duration"]
            text_str = " ".join([w["text"] for w in chunk_words])
            
            srt_content += f"{counter}\n"
            srt_content += f"{format_time(start_t)} --> {format_time(end_t)}\n"
            srt_content += f"{text_str}\n\n"
            counter += 1
            
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

    def generate_voiceover(self, text: str, voice_gender: str, language: str, output_path: str):
        """
        Generates TTS audio and an associated SRT file, saving to output_path.
        """
        gender = voice_gender if voice_gender in ["female", "male"] else "female"
        voice = VOICES[language][gender]
        
        asyncio.run(self._generate(text, voice, output_path))
        return output_path
