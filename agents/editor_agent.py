import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from config.settings import FORMATS

class EditorAgent:
    def __init__(self):
        pass

    def assemble_video(self, images: list, audio_path: str, format_type: str, output_path: str):
        """
        Combines images and voiceover into a video file.
        """
        # Load audio to get duration
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        
        # Calculate duration per image
        duration_per_image = total_duration / len(images) if images else 5.0

        resolution = (FORMATS[format_type]["width"], FORMATS[format_type]["height"])

        clips = []
        for img in images:
            # Create an ImageClip
            clip = ImageClip(img).set_duration(duration_per_image)
            # Resize it to fill the screen (this might distort, in a real app we'd crop/pad)
            clip = clip.resize(newsize=resolution)
            clips.append(clip)

        # Concatenate
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Add background music if available
        bgm_folder = "bgm"
        bgm_files = [f for f in os.listdir(bgm_folder) if f.endswith(".mp3")] if os.path.exists(bgm_folder) else []
        
        if bgm_files:
            import random
            from moviepy.editor import CompositeAudioClip
            from moviepy.audio.fx.all import volumex, audio_loop
            
            bgm_path = os.path.join(bgm_folder, random.choice(bgm_files))
            bgm_clip = AudioFileClip(bgm_path)
            # Loop bgm to match video duration and reduce volume to 10%
            bgm_clip = audio_loop(bgm_clip, duration=total_duration).fx(volumex, 0.1)
            
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
