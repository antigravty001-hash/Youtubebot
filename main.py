import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import os
import argparse
import random
import json
from datetime import datetime
from agents.research_agent import ResearchAgent
from agents.writer_agent import WriterAgent
from agents.voice_agent import VoiceAgent
from agents.visual_agent import VisualAgent
from agents.editor_agent import EditorAgent
from uploaders.youtube_uploader import YouTubeUploader

def load_settings():
    try:
        with open("data/settings.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_settings(settings):
    with open("data/settings.json", "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

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
    
    # Keep only last 50 logs
    logs = logs[:50]
    with open("data/logs.json", "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def produce_video(channel_type: str, language: str, format_type: str, dry_run: bool):
    print(f"--- Starting Production: {channel_type.upper()} | {language.upper()} | {format_type.upper()} ---")
    
    # Load settings to see if there's a custom topic or series
    settings = load_settings()
    chan_settings = settings.get(channel_type, {})
    
    topic_setting = chan_settings.get("topic", "auto")
    is_series = chan_settings.get("is_series", False)
    series_episode = chan_settings.get("series_episode", 1)

    # 1. Research / Topic Selection
    print("1. Determining topic...")
    
    # --- NEWS-JACKER: Auto-activate on 5th video of the day ---
    today_video_count = 0
    try:
        with open("data/logs.json", "r", encoding="utf-8") as f:
            all_logs = json.load(f)
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_video_count = sum(
            1 for log in all_logs
            if log.get("status") == "success"
            and log.get("timestamp", "").startswith(today_str)
        )
        print(f"[Daily Counter] Videos produced today so far: {today_video_count}")
    except Exception:
        pass
    
    use_news_mode = (today_video_count >= 4)  # 5th video (0-indexed: 0,1,2,3 done = this is #5)
    
    if topic_setting == "auto":
        from agents.data_scientist_agent import DataScientistAgent
        ds = DataScientistAgent()
        ds.analyze_channel(channel_type)
        
        if use_news_mode:
            # NEWS-JACKER MODE: 5th video of the day
            print("[News Agent] 🗞️ NEWS-JACKER MODE ACTIVATED (5th video of the day)")
            try:
                from agents.news_agent import NewsAgent
                news_agent = NewsAgent()
                topic = news_agent.get_news_topic(language)
                if not topic:
                    raise Exception("No headlines found")
            except Exception as e:
                print(f"[News Agent] ⚠️ News-Jacker failed ({e}), falling back to standard trend...")
                researcher = ResearchAgent()
                topic = researcher.get_topic(channel_type, language)
        else:
            # NORMAL MODE: Use YouTube trend research
            researcher = ResearchAgent()
            topic = researcher.get_topic(channel_type, language)
    else:
        topic = topic_setting
        if is_series:
            topic = f"{topic} (Part {series_episode})"

    print(f"Topic selected: {topic}")

    # 2. Write Script
    print("2. Generating script...")
    writer = WriterAgent()
    script = writer.write_script(topic, channel_type, language, format_type)
    print(f"Title: {script.get('title')}")

    # 3. Voiceover & Visuals
    print("3. Generating voiceover and downloading visuals...")
    voice_agent = VoiceAgent()
    visual_agent = VisualAgent()
    
    voice_gender = chan_settings.get("voice_gender", "female")
    visual_style = chan_settings.get("visual_style", "cinematic")
    
    os.makedirs("temp_assets", exist_ok=True)
    
    image_paths = []
    audio_paths = []
    
    for idx, scene in enumerate(script.get("scenes", [])):
        # 1. Generate Voiceover for this scene
        raw_text = scene.get("voiceover_text", "")
        # Clean text for TTS
        clean_text = raw_text.replace("*", "").replace("şşş", "").replace("hmm", "").replace("ahaha", "")
        if not clean_text.strip():
            clean_text = "..."
            
        scene_audio_path = f"temp_assets/voice_{channel_type}_{language}_{idx}.mp3"
        voice_agent.generate_voiceover(clean_text, voice_gender, language, scene_audio_path)
        audio_paths.append(scene_audio_path)
        
        # 2. Generate Visual for this scene
        visual_prompt = scene.get("visual_prompt", "nature")
        img_path = visual_agent.get_image(visual_prompt, channel_type, idx, visual_style)
        if img_path:
            image_paths.append(img_path)
        else:
            # Fallback image logic if visual generation completely fails
            fallback_path = "temp_assets/fallback.jpg"
            if not os.path.exists(fallback_path):
                import PIL.Image
                PIL.Image.new('RGB', (1080, 1920), color=(0, 0, 0)).save(fallback_path)
            image_paths.append(fallback_path)

    if not image_paths or len(image_paths) != len(audio_paths):
        raise Exception("Failed to generate synced media. Aborting.")

    # Generate Thumbnail
    from agents.thumbnail_agent import ThumbnailAgent
    thumb_agent = ThumbnailAgent()
    os.makedirs("output", exist_ok=True)
    thumb_path = f"output/{channel_type}_{language}_{format_type}_thumbnail.jpg"
    thumb_agent.create_thumbnail(image_paths[0], script.get("title", "İnanılmaz!"), thumb_path)

    # 4. Assembly
    print("4. Assembling video...")
    editor = EditorAgent()
    video_filename = f"output/{channel_type}_{language}_{format_type}.mp4"
    bgm_volume = float(chan_settings.get("bgm_volume", 0.1))
    editor.assemble_video(image_paths, audio_paths, format_type, video_filename, bgm_volume, channel_type)

    # 5. Upload
    video_url = None
    if not dry_run:
        print("5. Uploading to YouTube...")
        uploader = YouTubeUploader()
        video_id = uploader.upload(
            video_filename, 
            channel_type, 
            script.get("title", "Awesome Video"), 
            script.get("description", ""), 
            script.get("tags", [])
        )
        if video_id:
            video_url = f"https://youtube.com/watch?v={video_id}"
            
            # Upload Thumbnail
            if os.path.exists(thumb_path):
                print("5b. Uploading Thumbnail...")
                uploader.set_thumbnail(video_id, thumb_path, channel_type)
    else:
        print("5. Dry run enabled. Skipping upload.")
        video_url = "dry_run_no_url"

    # If successful and it was a series, increment episode count
    if is_series and video_url:
        chan_settings["series_episode"] = series_episode + 1
        settings[channel_type] = chan_settings
        save_settings(settings)
        
    append_log(channel_type, language, format_type, video_url=video_url)
    print("--- Production Complete ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Do not upload to YouTube")
    parser.add_argument("--channel", type=str, choices=["kids", "facts", "both"], default="both")
    # Instead of pulling lang and format from args, we will pull from settings.json if channel is specified
    args = parser.parse_args()

    channels = ["kids", "facts"] if args.channel == "both" else [args.channel]
    settings = load_settings()

    for c in channels:
        # Load from JSON or fallback to defaults
        c_settings = settings.get(c, {})
        lang = c_settings.get("language", "tr")
        fmt = c_settings.get("format", "shorts")
        
        try:
            produce_video(c, lang, fmt, args.dry_run)
        except Exception as e:
            print(f"Failed to produce video for {c}-{lang}-{fmt}: {e}")
            append_log(c, lang, fmt, error=e)
