from youtubesearchpython import VideosSearch
import random
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
        videos in the niche and extracts the title of a viral video.
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
            print(f"[Trend Agent] Scanning YouTube for niche: '{query}'...")
            
            # Using VideosSearch now that httpx proxy bug is fixed
            videos_search = VideosSearch(query, limit=15, region="TR" if language=="tr" else "US")
            results = videos_search.result()
            
            if results and 'result' in results:
                valid_videos = results['result']
                if valid_videos:
                    # Sort by views (approximate parsing since viewCount is text like '1.2M views')
                    # But the simplest is just taking the top 3 relevance which are already proven
                    top_video = random.choice(valid_videos[:3])
                    title = top_video.get('title', query)
                    views = top_video.get('viewCount', {}).get('short', 'Unknown views')
                    
                    print(f"[Trend Agent] 🎯 Found Viral Concept: '{title}' ({views})")
                    return f"VIRAL YOUTUBE CONCEPT: {title}"
                    
            print("[Trend Agent] No viral videos found. Falling back.")
            return f"Base Concept: {query}"
        except Exception as e:
            print(f"[Trend Agent] Search failed: {e}")
            return f"Base Concept: {query}"
