# -*- coding: utf-8 -*-
import os
import requests
import urllib.parse
import json
import random
import asyncio
import edge_tts
from datetime import datetime
import google.generativeai as genai

# Setup PIL compatibility just in case
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# Load Config
from config.settings import VOICES, FORMATS

class VoiceAgent3D:
    def __init__(self):
        self.rate = "-5%"
        self.pitch = "-5Hz"

    async def _generate(self, text: str, voice: str, output_path: str):
        communicate = edge_tts.Communicate(text, voice, rate=self.rate, pitch=self.pitch)
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
        gender = voice_gender if voice_gender in ["female", "male"] else "female"
        voice = VOICES[language][gender]
        asyncio.run(self._generate(text, voice, output_path))
        return output_path

class Editor3DAgent:
    def generate_eerie_drone(self, duration: float):
        import numpy as np
        from moviepy.audio.AudioClip import AudioArrayClip
        fps = 44100
        t = np.linspace(0, duration, int(fps*duration), False)
        audio = (np.sin(2 * np.pi * 110 * t) + np.sin(2 * np.pi * 112 * t)) * 0.05
        audio += np.sin(2 * np.pi * 165 * t) * 0.02
        stereo = np.vstack((audio, audio)).T
        return AudioArrayClip(stereo, fps=fps)

    def assemble_video(self, video_clips: list, audio_paths: list, format_type: str, output_path: str, bgm_volume: float = 0.1):
        resolution = (FORMATS[format_type]["width"], FORMATS[format_type]["height"])

        from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips, TextClip
        from moviepy.video.fx.all import crop, resize
        from moviepy.video.tools.subtitles import SubtitlesClip
        from moviepy.audio.fx.all import volumex

        whoosh_path = "temp_assets/whoosh.m4a"
        clips = []

        for idx, (media, aud) in enumerate(zip(video_clips, audio_paths)):
            try:
                from moviepy.editor import CompositeAudioClip
                audio_clip = AudioFileClip(aud)
                
                # Whoosh Transition Sound
                if idx > 0 and os.path.exists(whoosh_path):
                    try:
                        whoosh = AudioFileClip(whoosh_path)
                        if whoosh.duration > 1:
                            whoosh = whoosh.subclip(0, 1)
                        whoosh = whoosh.fx(volumex, 0.4)
                        audio_clip = CompositeAudioClip([audio_clip, whoosh])
                    except:
                        pass
                        
                duration_per_scene = audio_clip.duration
                if duration_per_scene is None or duration_per_scene <= 0:
                    duration_per_scene = 10.0
                    
                audio_clip = audio_clip.set_duration(duration_per_scene)
                
                # Process MP4 clip
                top_clip = VideoFileClip(media)
                if top_clip.duration is None or top_clip.duration < duration_per_scene:
                    from moviepy.video.fx.all import loop
                    top_clip = loop(top_clip, duration=duration_per_scene)
                else:
                    top_clip = top_clip.subclip(0, duration_per_scene)
                
                top_clip = top_clip.resize(height=resolution[1])
                w, h = top_clip.size
                top_clip = crop(top_clip, width=resolution[0], height=resolution[1], x_center=w/2)
                
                stacked = top_clip.set_duration(duration_per_scene)
                
                # Modern White Subtitles - Smaller and Lower per user specifications
                srt_path = aud.replace(".mp3", ".srt")
                if os.path.exists(srt_path) and os.path.getsize(srt_path) > 10:
                    try:
                        def generator(txt):
                            return TextClip(txt, fontsize=52, color='white', font='Impact',
                                            stroke_color='black', stroke_width=3, 
                                            size=(resolution[0]*0.9, None), method='caption')
                        
                        subtitles = SubtitlesClip(srt_path, generator)
                        # Position subtitles much lower (0.78 relative height)
                        subtitles = subtitles.set_position(('center', 0.78), relative=True)
                        stacked = CompositeVideoClip([stacked, subtitles]).set_duration(duration_per_scene)
                    except Exception as sub_err:
                        print(f"Failed to apply subtitles: {sub_err}")

                stacked = stacked.set_audio(audio_clip).set_duration(duration_per_scene)
                clips.append(stacked)
            except Exception as e:
                print(f"Error processing 3D scene {idx}: {e}")

        final_video = concatenate_videoclips(clips, method="compose")
        total_duration = final_video.duration
        
        # Procedural Background Drone
        drone_clip = self.generate_eerie_drone(total_duration)
        final_audio = CompositeAudioClip([final_video.audio, drone_clip]).set_duration(total_duration)
        final_video = final_video.set_audio(final_audio).set_duration(total_duration)

        # Render 3D Video
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
        final_video.close()
        return output_path

def append_log(channel, lang, format_type, video_url=None, error=None):
    try:
        with open("data/logs.json", "r", encoding="utf-8") as f:
            logs = json.load(f)
    except FileNotFoundError:
        logs = []
    
    logs.insert(0, {
        "timestamp": datetime.now().isoformat(),
        "channel": channel,
        "language": lang,
        "format": format_type,
        "status": "success" if video_url else "error",
        "video_url": video_url,
        "error_message": str(error) if error else None
    })
    
    logs = logs[:50]
    with open("data/logs.json", "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def download_3d_video(prompt: str, index: int, api_key: str) -> str:
    """Queries Pollinations AI Video Generation API to produce a 3D moving video clip"""
    os.makedirs("temp_assets", exist_ok=True)
    file_path = f"temp_assets/3d_vid_{index}.mp4"
    
    # Master-Level 3D Styling Prompt with high-quality movement, dynamic environment, and talking details
    enhanced_prompt = f"3D CGI animation, Pixar Disney style, fluid physics motion, vibrant colors, cinematic studio lighting, masterpiece, 8k resolution, {prompt}"
    print(f"[3D Visual Agent] Rendering scene {index} with prompt: {enhanced_prompt[:100]}...")
    
    safe_prompt = urllib.parse.quote(enhanced_prompt)
    url = f"https://gen.pollinations.ai/video/{safe_prompt}?key={api_key}"
    
    import time
    for attempt in range(4):
        try:
            # Video generation GET request is synchronous and blocks until fully rendered
            response = requests.get(url, timeout=180)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f"[3D Visual Agent] 🟢 Successfully rendered 3D clip for scene {index}!")
                return file_path
            else:
                print(f"[3D Visual Agent] API returned status code {response.status_code} (attempt {attempt+1})")
        except Exception as e:
            print(f"[3D Visual Agent] ⚠️ Connection failed (attempt {attempt+1}): {e}")
        time.sleep(5)
    return None

def main():
    print("=== Nexus 3D Video Generator MVP Starting ===")
    
    # Load settings
    try:
        with open("data/settings.json", "r", encoding="utf-8") as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {}
        
    facts_settings = settings.get("facts", {})
    language = facts_settings.get("language", "tr")
    format_type = facts_settings.get("format", "shorts")
    voice_gender = facts_settings.get("voice_gender", "male")
    
    # Retrieve API Keys
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    POLLINATIONS_API_KEY = os.environ.get("POLLINATIONS_API_KEY", "sk_3WGmGFNgPCHWVigvqrxpwLCFMEFlvWlq")
    
    if not GEMINI_API_KEY:
        print("[Error] GEMINI_API_KEY is not defined in environment variables.")
        return
        
    api_keys = [k.strip() for k in GEMINI_API_KEY.split(",") if k.strip()]
    
    # 1. Select absurd topic
    topic = "havuçtan ceket giyen ve konuşan adam modern aydınlık bir evde"
    print(f"Targeting Absurd 3D Topic: {topic}")

    # Write Senaryo (Senaryo 30-40 sn Shorts uzunluğunda olmalı - Yaklaşık 90-110 kelime)
    script_prompt = f"""
    You are a professional comedic AI scriptwriter.
    Write an incredibly absurd, funny, and engaging Shorts video script.
    Language: {language.upper()}
    CRITICAL RULE: The total voiceover duration must be around 30 to 40 seconds (aim for 90 to 110 words total).
    
    TOPIC: {topic}
    
    SCENARIO DIRECTIVES (ULTRA-QUALITY 3D SHORTS):
    - Visual setting: A luxury, bright modern house, packed with rich details, sunny daytime.
    - Character action: A stylized 3D character (man) wearing a high-fashion, detailed orange jacket made of carrots. The man must be actively speaking, gesturing dynamically, and reacting to the camera in every scene.
    - Weather/Lighting: Dynamic sunny daytime lighting matching the modern home setting.
    - Subtitle requirement: Do not use emojis in the voiceover_text.
    
    OUTPUT FORMAT: You MUST return a JSON object (no markdown formatting blocks).
    JSON structure:
    {{
        "title": "Absurd Title",
        "description": "Short description #3d #absurd",
        "tags": ["3d", "comedy", "funny", "shorts"],
        "scenes": [
            {{
                "visual_prompt": "Highly detailed English prompt describing the 3D talking character wearing the carrot jacket in a bright modern home setting, dynamic motion",
                "voiceover_text": "Spoken narrator/character text"
            }},
            ...
        ]
    }}
    """
    
    def parse_json_safely(raw_text):
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return json.loads(cleaned.strip())

    script = None

    # Resilient Multi-Provider script generation
    # A. Try Gemini
    try:
        print("[Gemini] 🔮 Attempting script generation...")
        random.shuffle(api_keys)
        model = None
        for api_key in api_keys:
            genai.configure(api_key=api_key)
            for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash', 'gemini-2.0-flash']:
                try:
                    test_model = genai.GenerativeModel(model_name)
                    response = test_model.generate_content(script_prompt)
                    script = parse_json_safely(response.text)
                    print(f"[Gemini] 🟢 Successfully generated script using {model_name}!")
                    break
                except:
                    continue
            if script:
                break
    except Exception as gemini_err:
        print(f"[Gemini] ⚠️ Failed: {gemini_err}. Trying Groq fallback...")

    # B. Try Groq (First Fallback)
    if not script:
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
        if GROQ_API_KEY:
            try:
                print("[Groq] ⚡ Attempting script generation with Groq...")
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama3-70b-8192",
                    "messages": [{"role": "user", "content": script_prompt}],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"}
                }
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    result_text = res.json()["choices"][0]["message"]["content"]
                    script = parse_json_safely(result_text)
                    print("[Groq] 🟢 Successfully generated script with Llama 3 70B!")
                else:
                    print(f"[Groq] API returned status code {res.status_code}")
            except Exception as groq_err:
                print(f"[Groq] ⚠️ Failed: {groq_err}. Trying OpenRouter fallback...")
        else:
            print("[Groq] ⚠️ GROQ_API_KEY is not defined. Skipping...")

    # C. Try OpenRouter (Second Fallback)
    if not script:
        OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
        if OPENROUTER_API_KEY:
            try:
                print("[OpenRouter] 🚀 Attempting script generation with OpenRouter...")
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/antigravty001-hash/Youtubebot"
                }
                payload = {
                    "model": "meta-llama/llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": script_prompt}],
                    "temperature": 0.7
                }
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    result_text = res.json()["choices"][0]["message"]["content"]
                    script = parse_json_safely(result_text)
                    print("[OpenRouter] 🟢 Successfully generated script with Llama 3.1 8B!")
                else:
                    print(f"[OpenRouter] API returned status code {res.status_code}")
            except Exception as or_err:
                print(f"[OpenRouter] ⚠️ Failed: {or_err}")
        else:
            print("[OpenRouter] ⚠️ OPENROUTER_API_KEY is not defined. Skipping...")

    if not script:
        print("[Error] All scriptwriter APIs (Gemini, Groq, OpenRouter) failed. Aborting production.")
        append_log("facts", language, format_type, error="All scriptwriter APIs failed.")
        return

    print(f"[Script] Final selected title: {script.get('title')}")

    # 2. Render 3D Video Clips via Pollinations Video API
    os.makedirs("temp_assets", exist_ok=True)
    video_clips = []
    audio_paths = []
    voice_agent = VoiceAgent3D()
    
    for idx, scene in enumerate(script.get("scenes", [])):
        print(f"\n--- Scene {idx+1} / {len(script.get('scenes'))} ---")
        
        # A. Voiceover Generation
        voice_text = scene.get("voiceover_text", "")
        audio_path = f"temp_assets/3d_voice_{idx}.mp3"
        print(f"[Voiceover] Generating speech: '{voice_text[:60]}...'")
        voice_agent.generate_voiceover(voice_text, voice_gender, language, audio_path)
        audio_paths.append(audio_path)
        
        # B. 3D Video Clip Generation
        visual_prompt = scene.get("visual_prompt", "A 3D character wearing a carrot jacket")
        clip_path = download_3d_video(visual_prompt, idx, POLLINATIONS_API_KEY)
        if clip_path:
            video_clips.append(clip_path)
        else:
            # Safe Fallback to image-to-video style if video endpoint fails
            print("[Fallback] Video generation failed. Creating robust dummy MP4 for assembly.")
            fallback_video = f"temp_assets/3d_fallback_{idx}.mp4"
            if not os.path.exists(fallback_video):
                # Download still image first
                safe_prompt = urllib.parse.quote(f"3D Pixar Disney style animation, highly detailed, {visual_prompt}")
                img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true&model=flux"
                img_data = requests.get(img_url).content
                img_path = f"temp_assets/fallback_img_{idx}.jpg"
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                
                # Make still image into 5-second video using FFmpeg
                import subprocess
                subprocess.run([
                    "ffmpeg", "-y", "-loop", "1", "-i", img_path, "-c:v", "libx264", "-t", "5", 
                    "-pix_fmt", "yuv420p", "-vf", "scale=1080:1920", fallback_video
                ], check=False, capture_output=True)
            video_clips.append(fallback_video)

    # 3. Compile and Assemble 3D Video (YouTube upload skipped)
    print("\n[Assembly] Staging compilation...")
    editor = Editor3DAgent()
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_output_path = f"output/3d_absurdity_{timestamp}.mp4"
    
    try:
        editor.assemble_video(video_clips, audio_paths, format_type, final_output_path)
        print(f"\n[Success] 🟢 3D video compiled successfully: {final_output_path}")
        # Log success with local inspect URL (YouTube upload skipped)
        append_log("facts", language, format_type, video_url="local_inspect_only")
    except Exception as e:
        print(f"[Error] Assembly failed: {e}")
        append_log("facts", language, format_type, error=f"Assembly failed: {e}")

if __name__ == "__main__":
    main()
