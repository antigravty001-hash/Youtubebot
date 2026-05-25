import os
from PIL import Image, ImageDraw, ImageFont

class ThumbnailAgent:
    def __init__(self):
        pass

    def create_thumbnail(self, base_image_path: str, title: str, output_path: str):
        print("[Thumbnail Agent] Creating highly clickable thumbnail...")
        try:
            try:
                img = Image.open(base_image_path)
            except Exception:
                # Fallback to black if base_image_path is missing or a video
                img = Image.new("RGB", (1280, 720), color="black")
                
            # Default YouTube horizontal format 1280x720
            img = img.resize((1280, 720))
            
            draw = ImageDraw.Draw(img)
            
            # Try to load a bold font, fallback to default
            try:
                # Windows common font
                font = ImageFont.truetype("impact.ttf", 90)
            except IOError:
                try:
                    # Ubuntu common font
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
                except IOError:
                    # Fallback
                    font = ImageFont.load_default()

            # Shorten title for thumbnail
            words = title.split()
            short_text = " ".join(words[:4]).upper() + "!"
            
            # Get text bounding box for centering
            bbox = draw.textbbox((0, 0), short_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (1280 - text_width) / 2
            y = 720 - text_height - 50 # Bottom placement
            
            # Draw black outline/shadow for contrast
            outline_color = "black"
            thickness = 5
            for adj_x in range(-thickness, thickness+1):
                for adj_y in range(-thickness, thickness+1):
                    draw.text((x+adj_x, y+adj_y), short_text, font=font, fill=outline_color)
            
            # Draw main text (Yellow for high clickability)
            draw.text((x, y), short_text, font=font, fill="yellow")
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path)
            print(f"[Thumbnail Agent] Thumbnail saved to {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[Thumbnail Agent] Failed to create thumbnail: {e}")
            return None
