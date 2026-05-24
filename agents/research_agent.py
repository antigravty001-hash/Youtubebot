from duckduckgo_search import DDGS
import random
from config.settings import THEMES

class ResearchAgent:
    def __init__(self):
        pass

    def get_topic(self, channel_type: str, language: str) -> str:
        """
        Picks a base theme and does a quick web search to find a trending sub-topic.
        """
        base_theme = random.choice(THEMES[channel_type])
        
        try:
            # Simple DDG search to find recent trends related to the base theme
            search_query = f"latest {base_theme}" if language == "en" else f"en yeni {base_theme} haberleri"
            results = list(DDGS().text(search_query, max_results=3))
            
            if results:
                # Pick the first result's title as inspiration
                trend_inspiration = results[0]['title']
                return f"Theme: {base_theme}. Inspiration from web: {trend_inspiration}"
            else:
                return base_theme
        except Exception as e:
            print(f"Search failed, falling back to base theme: {e}")
            return base_theme
