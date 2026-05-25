import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from config.settings import FORMATS

class EditorAgent:
    def __init__(self):
        pass

    def assemble_video(self, images: list, audio_paths: list, format_type: str, output_path: str, bgm_volume: float = 0.1, channel_type: str = "kids"):
        """
        Combines images and voiceover into a video file perfectly synced per scene.
        """
        resolution = (FORMATS[format_type]["width"], FORMATS[format_type]["height"])

        from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips
        from moviepy.video.fx.all import crop

        clips = []
        for media, aud in zip(images, audio_paths):
            try:
                audio_clip = AudioFileClip(aud)
                duration_per_image = audio_clip.duration
                
                if media.endswith(".mp4"):
                    clip = VideoFileClip(media)
                    if clip.duration < duration_per_image:
                        from moviepy.video.fx.all import loop
                        clip = loop(clip, duration=duration_per_image)
                    else:
                        clip = clip.subclip(0, duration_per_image)
                    
                    clip = clip.resize(height=resolution[1])
                    w, h = clip.size
                    clip = crop(clip, width=resolution[0], height=resolution[1], x_center=w/2)
                else:
                    clip = ImageClip(media).set_duration(duration_per_image)
                    clip = clip.resize(height=resolution[1])
                    clip = clip.resize(lambda t: 1 + 0.1 * (t / duration_per_image))
                    clip = clip.set_position(('center', 'center'))
                    clip = CompositeVideoClip([clip], size=resolution)
                    
                # Bind audio to the clip
                clip = clip.set_audio(audio_clip)
                clips.append(clip)
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
        
        final_video.close()
        return output_path
