from youtubesearchpython import VideosSearch
import random

class ResearchAgent:
    def __init__(self):
        # Niche queries to scan for viral concepts
        self.queries = {
            "kids": {
                "tr": ["çocuk masalları", "eğitici animasyon çocuk", "çocuklar için hikaye", "çocuk şarkıları hikayeli"],
                "en": ["bedtime stories for kids", "kids educational animation", "fun kids stories", "moral stories for kids"]
            },
            "facts": {
                "tr": ["ilginç tarihi gerçekler", "az bilinen gerçekler", "tarihin sırları", "dünyanın en tuhaf olayları", "uzay hakkında şaşırtıcı bilgiler"],
                "en": ["weird history facts", "mind blowing facts", "unsolved historical mysteries", "crazy space facts", "unknown animal facts"]
            }
        }

    def get_topic(self, channel_type: str, language: str) -> str:
        """
        Acts as a Real-Time Trend Tracker. Searches YouTube for highly relevant and popular
        videos in the niche and extracts the title of a viral video as inspiration.
        """
        query_list = self.queries.get(channel_type, {}).get(language, ["trending stories"])
        
        # Integrate Data Scientist Insights
        try:
            import json
            with open("data/insights.json", "r", encoding="utf-8") as f:
                insights = json.load(f)
                if channel_type in insights:
                    top_concepts = insights[channel_type].get("top_performing_concepts", [])
                    if top_concepts:
                        print(f"[Trend Agent] Boosting search with top historical concepts: {top_concepts}")
                        # We heavily weight historical successes (50% chance to search based on a past successful video title)
                        query_list.extend(top_concepts * 2)
        except Exception:
            pass

        query = random.choice(query_list)
        
        try:
            print(f"[Trend Agent] Scanning YouTube for niche: '{query}'...")
            videos_search = VideosSearch(query, limit=10, region="TR" if language=="tr" else "US")
            results = videos_search.result()
            
            if results and 'result' in results:
                valid_videos = results['result']
                if valid_videos:
                    # YouTube relevance algorithm already puts highly successful/viral videos at the top.
                    # We pick one of the top 3 to maintain variety but guarantee a proven concept.
                    top_video = random.choice(valid_videos[:3])
                    title = top_video.get('title', query)
                    views = top_video.get('viewCount', {}).get('short', 'Unknown views')
                    
                    print(f"[Trend Agent] 🎯 Found Viral Concept: '{title}' ({views})")
                    return f"VIRAL YOUTUBE CONCEPT: {title}"
                    
            return f"Base Concept: {query}" # Fallback
        except Exception as e:
            print(f"[Trend Agent] Search failed: {e}")
            return f"Base Concept: {query}" # Fallback
