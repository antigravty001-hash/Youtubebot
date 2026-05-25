import asyncio
import edge_tts
import os
from config.settings import VOICES

class VoiceAgent:
    def __init__(self):
        # Locked for "Unknown Archives" (dark, deep, serious tone)
        self.rate = "-5%"
        self.pitch = "-5Hz"

    async def _generate(self, text: str, voice: str, output_path: str):
        communicate = edge_tts.Communicate(text, voice, rate=self.rate, pitch=self.pitch)
        
        # We will manually collect boundaries to create subtitles
        boundaries = []
        
        with open(output_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] in ["WordBoundary", "SentenceBoundary"]:
                    boundaries.append(chunk)

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
        counter = 1
        
        # Check if we got word boundaries or sentence boundaries
        is_word_level = all(b["type"] == "WordBoundary" for b in boundaries) if boundaries else False
        
        if is_word_level:
            chunk_size = 3
            for i in range(0, len(boundaries), chunk_size):
                chunk_words = boundaries[i:i+chunk_size]
                if not chunk_words: continue
                
                start_t = chunk_words[0]["offset"]
                end_t = chunk_words[-1]["offset"] + chunk_words[-1]["duration"]
                text_str = " ".join([w["text"] for w in chunk_words])
                
                srt_content += f"{counter}\n"
                srt_content += f"{format_time(start_t)} --> {format_time(end_t)}\n"
                srt_content += f"{text_str}\n\n"
                counter += 1
        else:
            # Fallback to SentenceBoundary or individual chunks
            for b in boundaries:
                start_t = b["offset"]
                end_t = b["offset"] + b["duration"]
                text_str = b["text"]
                
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
