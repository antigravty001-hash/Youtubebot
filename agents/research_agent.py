import random
import subprocess
import json

class ResearchAgent:
    def __init__(self):
        # Niche queries to scan for viral concepts (Facts only since we dropped Kids)
        self.queries = {
            "tr": ["ilginç tarihi gerçekler", "uzay belgeseli gizem", "tarihin sırları", "dünyanın en tuhaf olayları", "korkunç uzay gerçekleri"],
            "en": ["weird history facts", "mind blowing facts", "unsolved historical mysteries", "terrifying space facts", "unknown dark facts"]
        }

    def get_topic(self, channel_type: str, language: str) -> str:
        """
        Acts as a Real-Time Trend Tracker. Searches YouTube for highly relevant and popular
        videos in the niche from the LAST 3 DAYS and extracts the title of a viral video.
        """
        query_list = self.queries.get(language, ["trending mysteries"])
        
        # Integrate Data Scientist Insights
        try:
            with open("data/insights.json", "r", encoding="utf-8") as f:
                insights = json.load(f)
                if channel_type in insights:
                    top_concepts = insights[channel_type].get("top_performing_concepts", [])
                    if top_concepts:
                        print(f"[Trend Agent] Boosting search with top historical concepts: {top_concepts}")
                        query_list.extend(top_concepts * 2)
        except Exception:
            pass

        query = random.choice(query_list)
        
        try:
            print(f"[Trend Agent] Scanning YouTube (Last 3 Days) for niche: '{query}'...")
            
            # Use yt-dlp to search for the top 5 videos uploaded in the last 3 days
            cmd = [
                "yt-dlp",
                f"ytsearch5:{query}",
                "--dateafter", "now-3days",
                "--dump-json",
                "--no-warnings"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            valid_videos = []
            for line in result.stdout.strip().split('\n'):
                if not line: continue
                try:
                    video_data = json.loads(line)
                    title = video_data.get('title', '')
                    views = video_data.get('view_count', 0)
                    if title:
                        valid_videos.append({'title': title, 'views': views})
                except json.JSONDecodeError:
                    continue
                    
            if valid_videos:
                # Sort by views to find the most viral one in the last 3 days
                valid_videos.sort(key=lambda x: x['views'], reverse=True)
                top_video = valid_videos[0]
                
                print(f"[Trend Agent] 🎯 Found Viral Concept (Last 3 Days): '{top_video['title']}' ({top_video['views']} views)")
                return f"VIRAL YOUTUBE CONCEPT: {top_video['title']}"
                
            print("[Trend Agent] No viral videos found in the last 3 days for this query. Falling back.")
            return f"Base Concept: {query}"
        except Exception as e:
            print(f"[Trend Agent] Search failed: {e}")
            return f"Base Concept: {query}"
