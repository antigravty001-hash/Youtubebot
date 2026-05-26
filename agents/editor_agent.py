import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from config.settings import FORMATS

class EditorAgent:
    def __init__(self):
        pass

    def generate_eerie_drone(self, duration: float):
        import numpy as np
        from moviepy.audio.AudioClip import AudioArrayClip
        fps = 44100
        t = np.linspace(0, duration, int(fps*duration), False)
        # 110Hz (A2) and 112Hz to create a beating/pulsing eerie effect for phones
        audio = (np.sin(2 * np.pi * 110 * t) + np.sin(2 * np.pi * 112 * t)) * 0.05
        # Add a higher dissonant harmonic for extra creepiness
        audio += np.sin(2 * np.pi * 165 * t) * 0.02
        stereo = np.vstack((audio, audio)).T
        return AudioArrayClip(stereo, fps=fps)

    def assemble_video(self, images: list, audio_paths: list, format_type: str, output_path: str, bgm_volume: float = 0.1, channel_type: str = "kids"):
        """
        Combines images, voiceover, satisfying background, and subtitles into a TikTok-style split screen video.
        """
        resolution = (FORMATS[format_type]["width"], FORMATS[format_type]["height"])

        from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips, TextClip, clips_array
        from moviepy.video.fx.all import crop, resize
        from moviepy.video.tools.subtitles import SubtitlesClip
        
        from moviepy.video.tools.subtitles import SubtitlesClip

        # --- DOWNLOAD WHOOSH SFX ---
        whoosh_path = "temp_assets/whoosh.m4a"
        if not os.path.exists("temp_assets/whoosh.m4a"):
            import subprocess
            try:
                print("Downloading whoosh sound effect...")
                subprocess.run([
                    "yt-dlp",
                    "ytsearch1:whoosh transition sound effect short",
                    "-f", "bestaudio",
                    "--max-downloads", "1",
                    "-o", "temp_assets/whoosh.m4a"
                ], check=False, capture_output=True) # check=False because max-downloads causes exit code 101
            except Exception as e:
                print(f"Failed to download whoosh: {e}")

        clips = []

        for idx, (media, aud) in enumerate(zip(images, audio_paths)):
            try:
                from moviepy.editor import CompositeAudioClip
                audio_clip = AudioFileClip(aud)
                
                # --- ADD WHOOSH SFX ---
                if idx > 0 and os.path.exists(whoosh_path):
                    try:
                        whoosh = AudioFileClip(whoosh_path)
                        if whoosh.duration > 1:
                            whoosh = whoosh.subclip(0, 1) # Keep it short
                        from moviepy.audio.fx.all import volumex
                        whoosh = whoosh.fx(volumex, 0.5) # Lower volume
                        audio_clip = CompositeAudioClip([audio_clip, whoosh])
                    except:
                        pass
                        
                duration_per_image = audio_clip.duration
                if duration_per_image is None or duration_per_image <= 0:
                    # Fallback to reading duration from SRT file
                    srt_path = aud.replace(".mp3", ".srt")
                    if os.path.exists(srt_path):
                        with open(srt_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            for line in reversed(lines):
                                if "-->" in line:
                                    end_time_str = line.split("-->")[1].strip()
                                    h, m, s_ms = end_time_str.split(":")
                                    s, ms = s_ms.split(",")
                                    duration_per_image = int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0
                                    break
                if duration_per_image is None or duration_per_image <= 0:
                    duration_per_image = 10.0 # Absolute fallback
                    
                # Explicitly set audio clip duration to prevent NoneType downstream
                audio_clip = audio_clip.set_duration(duration_per_image)
                
                # --- FULL SCREEN (AI Image/Video) ---
                if media.endswith(".mp4"):
                    top_clip = VideoFileClip(media)
                    if top_clip.duration is None or top_clip.duration < duration_per_image:
                        from moviepy.video.fx.all import loop
                        top_clip = loop(top_clip, duration=duration_per_image)
                    else:
                        top_clip = top_clip.subclip(0, duration_per_image)
                    
                    top_clip = top_clip.resize(height=resolution[1])
                    w, h = top_clip.size
                    top_clip = crop(top_clip, width=resolution[0], height=resolution[1], x_center=w/2)
                else:
                    from moviepy.editor import ImageClip
                    top_clip = ImageClip(media).set_duration(duration_per_image)
                    top_clip = top_clip.resize(height=resolution[1])
                    top_clip = top_clip.resize(lambda t: 1 + 0.1 * (t / duration_per_image))
                    top_clip = top_clip.set_position(('center', 'center'))
                    top_clip = CompositeVideoClip([top_clip], size=resolution).set_duration(duration_per_image)
                
                # --- NO SPLIT SCREEN, TOP CLIP IS THE ONLY VISUAL ---
                stacked = top_clip.set_duration(duration_per_image)
                
                # --- SUBTITLES ---
                srt_path = aud.replace(".mp3", ".srt")
                if os.path.exists(srt_path) and os.path.getsize(srt_path) > 10:
                    try:
                        # Generator for TextClip (Yellow, thicker stroke for dark backgrounds)
                        def generator(txt):
                            return TextClip(txt, fontsize=85, color='yellow', font='Impact',
                                            stroke_color='black', stroke_width=4, 
                                            size=(resolution[0]*0.9, None), method='caption')
                        
                        subtitles = SubtitlesClip(srt_path, generator)
                        # Position subtitles slightly below the center of the screen
                        subtitles = subtitles.set_position(('center', 0.65), relative=True)
                        stacked = CompositeVideoClip([stacked, subtitles]).set_duration(duration_per_image)
                    except Exception as sub_err:
                        print(f"Failed to apply subtitles from {srt_path}: {sub_err}")

                # Bind audio to the clip
                stacked = stacked.set_audio(audio_clip).set_duration(duration_per_image)
                clips.append(stacked)
            except Exception as e:
                print(f"Error processing scene: {e}")

        # Concatenate all synced scenes
        final_video = concatenate_videoclips(clips, method="compose")
        total_duration = final_video.duration
        
        # Procedural Eerie Drone Background Music (Royalty Free)
        from moviepy.editor import CompositeAudioClip
        drone_clip = self.generate_eerie_drone(total_duration)
        final_audio = CompositeAudioClip([final_video.audio, drone_clip]).set_duration(total_duration)
        final_video = final_video.set_audio(final_audio).set_duration(total_duration)

        # Export
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
        final_video.close()
        return output_path
