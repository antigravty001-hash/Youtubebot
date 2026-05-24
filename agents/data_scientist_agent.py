import json
import os
from uploaders.youtube_uploader import YouTubeUploader

class DataScientistAgent:
    def __init__(self):
        self.insights_file = "data/insights.json"
        
    def analyze_channel(self, channel_type: str):
        print(f"[Data Scientist] Analyzing performance for {channel_type} channel...")
        try:
            uploader = YouTubeUploader()
            youtube = uploader.get_service(channel_type)
            if not youtube:
                print("[Data Scientist] Skipping analysis: Not authenticated.")
                return

            # Find the top 5 most viewed videos for this channel
            request = youtube.search().list(
                part="snippet",
                forMine=True,
                type="video",
                order="viewCount",
                maxResults=5
            )
            response = request.execute()
            
            top_topics = []
            for item in response.get("items", []):
                title = item["snippet"]["title"]
                top_topics.append(title)
                
            if not top_topics:
                print("[Data Scientist] No videos found on the channel yet.")
                return
                
            # Load existing insights
            try:
                with open(self.insights_file, "r", encoding="utf-8") as f:
                    insights = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                insights = {}
                
            insights[channel_type] = {
                "top_performing_concepts": top_topics
            }
            
            os.makedirs("data", exist_ok=True)
            with open(self.insights_file, "w", encoding="utf-8") as f:
                json.dump(insights, f, indent=2, ensure_ascii=False)
                
            print(f"[Data Scientist] Success! Top concepts for {channel_type}: {top_topics}")
            
        except Exception as e:
            print(f"[Data Scientist] Analysis failed: {e}")
