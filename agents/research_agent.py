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
                    # Parse views to integers
                    def get_views(v):
                        try:
                            views_data = v.get('viewCount', {})
                            if isinstance(views_data, dict):
                                text = views_data.get('text', '0')
                                return int(''.join(filter(str.isdigit, text)))
                        except:
                            pass
                        return 0
                    
                    # Sort videos by actual view count
                    valid_videos.sort(key=get_views, reverse=True)
                    
                    # Filter for highly viral videos (> 500K views)
                    viral_videos = [v for v in valid_videos if get_views(v) >= 500000]
                    
                    if viral_videos:
                        top_video = random.choice(viral_videos[:5]) # Pick from top viral ones
                    else:
                        top_video = valid_videos[0] # Fallback to the most viewed one available
                        
                    title = top_video.get('title', query)
                    views_data = top_video.get('viewCount', {})
                    if not isinstance(views_data, dict):
                        views_data = {}
                    views = views_data.get('short', 'Unknown views')
                    if views is None:
                        views = 'Unknown views'
                    
                    print(f"[Trend Agent] 🎯 Found Viral Concept: '{title}' ({views})")
                    return f"VIRAL YOUTUBE CONCEPT: {title}"
                    
            print("[Trend Agent] No viral videos found. Falling back.")
            return f"Base Concept: {query}"
        except Exception as e:
            print(f"[Trend Agent] Search failed: {e}")
            return f"Base Concept: {query}"
