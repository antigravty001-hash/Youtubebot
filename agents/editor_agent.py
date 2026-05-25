import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from config.settings import FORMATS

class EditorAgent:
    def __init__(self):
        pass

    def download_satisfying_bg(self):
        import subprocess
        import random
        import glob
        
        # Clean up old bg videos to save space
        old_files = glob.glob("temp_assets/bg_vid.*")
        for f in old_files:
            try:
                os.remove(f)
            except:
                pass
                
        queries = ["gta 5 parkour shorts", "minecraft parkour shorts", "kinetic sand satisfying shorts"]
        query = random.choice(queries)
        print(f"Downloading background video for query: {query}")
        
        try:
            cmd = [
                "yt-dlp",
                f"ytsearch1:{query}",
                "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                "--max-downloads", "1",
                "--match-filter", "duration < 120",
                "-o", "temp_assets/bg_vid.%(ext)s"
            ]
            subprocess.run(cmd, check=True)
            files = glob.glob("temp_assets/bg_vid.*")
            if files:
                return files[0]
        except Exception as e:
            print(f"Failed to download bg video: {e}")
        return None

    def assemble_video(self, images: list, audio_paths: list, format_type: str, output_path: str, bgm_volume: float = 0.1, channel_type: str = "kids"):
        """
        Combines images, voiceover, satisfying background, and subtitles into a TikTok-style split screen video.
        """
        resolution = (FORMATS[format_type]["width"], FORMATS[format_type]["height"])

        from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips, TextClip, clips_array
        from moviepy.video.fx.all import crop, resize
        from moviepy.video.tools.subtitles import SubtitlesClip
        
        # Determine half-screen resolution for top and bottom
        half_res = (resolution[0], resolution[1] // 2)

        # 1. Download Background Video for Bottom Half
        bg_vid_path = self.download_satisfying_bg()
        bg_full_clip = None
        if bg_vid_path:
            try:
                bg_full_clip = VideoFileClip(bg_vid_path).without_audio()
                # Ensure it fills the half screen proportionally
                w_ratio = half_res[0] / bg_full_clip.size[0]
                h_ratio = half_res[1] / bg_full_clip.size[1]
                ratio = max(w_ratio, h_ratio)
                
                bg_full_clip = bg_full_clip.resize(ratio)
                w, h = bg_full_clip.size
                bg_full_clip = crop(bg_full_clip, width=half_res[0], height=half_res[1], x_center=w/2, y_center=h/2)
            except Exception as e:
                print(f"Error loading background video: {e}")
                bg_full_clip = None

        # --- DOWNLOAD WHOOSH SFX ---
        whoosh_path = "temp_assets/whoosh.m4a"
        if not os.path.exists(whoosh_path):
            import subprocess
            try:
                print("Downloading whoosh sound effect...")
                subprocess.run(["yt-dlp", "ytsearch1:whoosh transition sound effect short", "-f", "bestaudio", "--max-downloads", "1", "-o", whoosh_path], check=True)
            except Exception as e:
                print(f"Failed to download whoosh: {e}")

        clips = []
        current_bg_time = 0
        
        # Initialize continuous background tracker
        if bg_full_clip:
            import random
            total_needed_duration = sum(AudioFileClip(a).duration for a in audio_paths)
            if bg_full_clip.duration > total_needed_duration:
                current_bg_time = random.uniform(0, bg_full_clip.duration - total_needed_duration)

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
                
                # --- TOP HALF (AI Image/Video) ---
                if media.endswith(".mp4"):
                    top_clip = VideoFileClip(media)
                    if top_clip.duration < duration_per_image:
                        from moviepy.video.fx.all import loop
                        top_clip = loop(top_clip, duration=duration_per_image)
                    else:
                        top_clip = top_clip.subclip(0, duration_per_image)
                    
                    top_clip = top_clip.resize(height=half_res[1])
                    w, h = top_clip.size
                    top_clip = crop(top_clip, width=half_res[0], height=half_res[1], x_center=w/2)
                else:
                    from moviepy.editor import ImageClip, ColorClip
                    try:
                        top_clip = ImageClip(media).set_duration(duration_per_image)
                        top_clip = top_clip.resize(height=half_res[1])
                        top_clip = top_clip.resize(lambda t: 1 + 0.1 * (t / duration_per_image))
                        top_clip = top_clip.set_position(('center', 'center'))
                        top_clip = CompositeVideoClip([top_clip], size=half_res)
                    except Exception as e:
                        print(f"Image load failed for {media}, using black screen: {e}")
                        top_clip = ColorClip(size=half_res, color=(0,0,0)).set_duration(duration_per_image)
                
                # --- BOTTOM HALF (Satisfying Video) ---
                if bg_full_clip:
                    # Continuous clip playing
                    if bg_full_clip.duration > current_bg_time + duration_per_image:
                        bottom_clip = bg_full_clip.subclip(current_bg_time, current_bg_time + duration_per_image)
                        current_bg_time += duration_per_image
                    else:
                        from moviepy.video.fx.all import loop
                        bottom_clip = loop(bg_full_clip, duration=duration_per_image)
                else:
                    # Fallback to black if download failed
                    from moviepy.editor import ColorClip
                    bottom_clip = ColorClip(size=half_res, color=(0,0,0)).set_duration(duration_per_image)

                # --- SPLIT SCREEN ASSEMBLY ---
                stacked = clips_array([[top_clip], [bottom_clip]])
                
                # --- SUBTITLES ---
                srt_path = aud.replace(".mp3", ".srt")
                if os.path.exists(srt_path):
                    # Generator for TextClip
                    def generator(txt):
                        return TextClip(txt, fontsize=70, color='white', 
                                        stroke_color='black', stroke_width=3, 
                                        size=(resolution[0]*0.9, None), method='caption')
                    
                    subtitles = SubtitlesClip(srt_path, generator)
                    # Position subtitles at the center of the entire screen
                    subtitles = subtitles.set_position(('center', 'center'))
                    stacked = CompositeVideoClip([stacked, subtitles])

                # Bind audio to the clip
                stacked = stacked.set_audio(audio_clip)
                clips.append(stacked)
            except Exception as e:
                print(f"Error processing scene: {e}")

        # Concatenate all synced scenes
        final_video = concatenate_videoclips(clips, method="compose")
        total_duration = final_video.duration
        
        # Add background music if available
        bgm_folder = f"bgm/{channel_type}"
        bgm_files = [f for f in os.listdir(bgm_folder) if f.endswith((".mp3", ".m4a", ".webm"))] if os.path.exists(bgm_folder) else []
        
        if bgm_files:
            import random
            from moviepy.editor import CompositeAudioClip
            from moviepy.audio.fx.all import volumex, audio_loop
            
            bgm_path = os.path.join(bgm_folder, random.choice(bgm_files))
            bgm_clip = AudioFileClip(bgm_path)
            bgm_clip = audio_loop(bgm_clip, duration=total_duration).fx(volumex, bgm_volume)
            
            # Mix voiceover (which is already in final_video) and bgm
            final_audio = CompositeAudioClip([final_video.audio, bgm_clip])
            final_video = final_video.set_audio(final_audio)

        # Export
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
        
        if bg_full_clip:
            bg_full_clip.close()
        final_video.close()
        return output_path
