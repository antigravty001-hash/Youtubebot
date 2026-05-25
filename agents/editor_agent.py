import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from config.settings import FORMATS

class EditorAgent:
    def __init__(self):
        pass

    def assemble_video(self, images: list, audio_path: str, format_type: str, output_path: str, bgm_volume: float = 0.1, channel_type: str = "kids"):
        """
        Combines images and voiceover into a video file.
        """
        # Load audio to get duration
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        
        # Calculate duration per image
        duration_per_image = total_duration / len(images) if images else 5.0

        resolution = (FORMATS[format_type]["width"], FORMATS[format_type]["height"])

        from moviepy.editor import VideoFileClip, CompositeVideoClip
        from moviepy.video.fx.all import crop

        clips = []
        for media in images:
            if media.endswith(".mp4"):
                try:
                    clip = VideoFileClip(media)
                    # Loop or cut to duration
                    if clip.duration < duration_per_image:
                        from moviepy.video.fx.all import loop
                        clip = loop(clip, duration=duration_per_image)
                    else:
                        clip = clip.subclip(0, duration_per_image)
                    
                    # Resize to fill height, then crop center to fix aspect ratio
                    clip = clip.resize(height=resolution[1])
                    w, h = clip.size
                    clip = crop(clip, width=resolution[0], height=resolution[1], x_center=w/2)
                    clips.append(clip)
                except Exception as e:
                    print(f"Error loading video clip {media}: {e}")
            else:
                # Create an ImageClip with Ken Burns Zoom Effect
                clip = ImageClip(media).set_duration(duration_per_image)
                # 1. Resize base to fill height
                clip = clip.resize(height=resolution[1])
                # 2. Apply zoom effect (1.0 to 1.1)
                clip = clip.resize(lambda t: 1 + 0.1 * (t / duration_per_image))
                # 3. Center and wrap in CompositeVideoClip to enforce exact resolution
                clip = clip.set_position(('center', 'center'))
                clip = CompositeVideoClip([clip], size=resolution)
                clips.append(clip)

        # Concatenate
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Add background music if available
        bgm_folder = f"bgm/{channel_type}"
        bgm_files = [f for f in os.listdir(bgm_folder) if f.endswith((".mp3", ".m4a", ".webm"))] if os.path.exists(bgm_folder) else []
        
        if bgm_files:
            import random
            from moviepy.editor import CompositeAudioClip
            from moviepy.audio.fx.all import volumex, audio_loop
            
            bgm_path = os.path.join(bgm_folder, random.choice(bgm_files))
            bgm_clip = AudioFileClip(bgm_path)
            # Loop bgm to match video duration and apply user volume
            bgm_clip = audio_loop(bgm_clip, duration=total_duration).fx(volumex, bgm_volume)
            
            # Mix voiceover and bgm
            final_audio = CompositeAudioClip([audio_clip, bgm_clip])
            final_video = final_video.set_audio(final_audio)
        else:
            final_video = final_video.set_audio(audio_clip)

        # Export
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
        
        # Close clips to free memory
        audio_clip.close()
        final_video.close()
        
        return output_path
