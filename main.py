import os
import argparse
import random
from agents.research_agent import ResearchAgent
from agents.writer_agent import WriterAgent
from agents.voice_agent import VoiceAgent
from agents.visual_agent import VisualAgent
from agents.editor_agent import EditorAgent
from uploaders.youtube_uploader import YouTubeUploader

def produce_video(channel_type: str, language: str, format_type: str, dry_run: bool):
    print(f"--- Starting Production: {channel_type.upper()} | {language.upper()} | {format_type.upper()} ---")
    
    # 1. Research
    print("1. Researching topic...")
    researcher = ResearchAgent()
    topic = researcher.get_topic(channel_type, language)
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
    
    os.makedirs("temp_assets", exist_ok=True)
    voice_path = f"temp_assets/voice_{channel_type}_{language}.mp3"
    
    # Combine all voiceover texts
    full_text = " ".join([scene.get("voiceover_text", "") for scene in script.get("scenes", [])])
    voice_agent.generate_voiceover(full_text, channel_type, language, voice_path)

    image_paths = []
    for idx, scene in enumerate(script.get("scenes", [])):
        visual_prompt = scene.get("visual_prompt", "nature")
        img_path = visual_agent.get_image(visual_prompt, channel_type, idx)
        if img_path:
            image_paths.append(img_path)

    if not image_paths:
        print("Failed to get any images. Aborting.")
        return

    # 4. Assembly
    print("4. Assembling video...")
    editor = EditorAgent()
    os.makedirs("output", exist_ok=True)
    video_filename = f"output/{channel_type}_{language}_{format_type}.mp4"
    editor.assemble_video(image_paths, voice_path, format_type, video_filename)

    # 5. Upload
    if not dry_run:
        print("5. Uploading to YouTube...")
        uploader = YouTubeUploader()
        uploader.upload(
            video_filename, 
            channel_type, 
            script.get("title", "Awesome Video"), 
            script.get("description", ""), 
            script.get("tags", [])
        )
    else:
        print("5. Dry run enabled. Skipping upload.")

    print("--- Production Complete ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Do not upload to YouTube")
    parser.add_argument("--channel", type=str, choices=["kids", "facts", "both"], default="both")
    parser.add_argument("--format", type=str, choices=["shorts", "long", "both"], default="shorts")
    parser.add_argument("--lang", type=str, choices=["en", "tr", "both"], default="both")
    args = parser.parse_args()

    channels = ["kids", "facts"] if args.channel == "both" else [args.channel]
    formats = ["shorts", "long"] if args.format == "both" else [args.format]
    langs = ["en", "tr"] if args.lang == "both" else [args.lang]

    for c in channels:
        for f in formats:
            for l in langs:
                try:
                    produce_video(c, l, f, args.dry_run)
                except Exception as e:
                    print(f"Failed to produce video for {c}-{l}-{f}: {e}")
