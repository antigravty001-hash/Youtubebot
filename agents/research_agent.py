from youtubesearchpython import VideosSearch
import random
import json
import os
import google.generativeai as genai
from config.settings import GEMINI_API_KEY

class ResearchAgent:
    def __init__(self):
        # We will use Gemini to generate dynamic search queries.
        self.api_keys = [k.strip() for k in GEMINI_API_KEY.split(",") if k.strip()]

    def _get_dynamic_queries(self, language: str) -> list:
        prompt = f"""
        You are a YouTube trends analyst. We run a 'Dark History / Mystery / Unknown Facts' Shorts channel.
        Generate a JSON array of 5 highly specific, viral, and obscure search queries in {language.upper()} language.
        Do NOT use generic terms like 'weird history facts'. Use highly specific concepts that people are currently obsessed with, such as:
        - Specific unexplained disappearances
        - Terrifying space anomalies discovered recently
        - Creepy historical artifacts
        - Declassified government secrets
        
        Return ONLY a raw JSON array of 5 strings. Example: ["the dyatlov pass incident new evidence", "scary deep ocean sounds", ...]
        """
        
        random.shuffle(self.api_keys)
        for api_key in self.api_keys:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                
                cleaned = response.text.strip()
                if cleaned.startswith("```json"): cleaned = cleaned[7:]
                elif cleaned.startswith("```"): cleaned = cleaned[3:]
                if cleaned.endswith("```"): cleaned = cleaned[:-3]
                
                queries = json.loads(cleaned.strip())
                if isinstance(queries, list) and len(queries) > 0:
                    return queries
            except Exception as e:
                print(f"[Research Agent] Failed to generate dynamic queries with key {api_key[-4:]}: {e}")
                continue
                
        # Fallback queries if API fails
        return {
            "tr": ["gizli kalmış tarihi sır", "uzayın derinliklerindeki korkunç gerçekler", "dünyanın açıklanamayan olayları"],
            "en": ["unsolved terrifying mystery", "creepy space anomalies", "declassified dark secrets"]
        }.get(language, ["trending mysteries"])

    def get_topic(self, channel_type: str, language: str) -> str:
        """
        Acts as a Real-Time Trend Tracker. Generates dynamic queries via AI, searches YouTube for highly relevant and popular
        videos in the niche and extracts the title of a viral video.
        """
        print("[Trend Agent] Asking AI for today's viral niche concepts...")
        query_list = self._get_dynamic_queries(language)
        
        # Integrate Data Scientist Insights
        try:
            with open("data/insights.json", "r", encoding="utf-8") as f:
                insights = json.load(f)
                if channel_type in insights:
                    top_concepts = insights[channel_type].get("top_performing_concepts", [])
                    if top_concepts:
                        print(f"[Trend Agent] Boosting search with top historical concepts: {top_concepts}")
                        query_list.extend(top_concepts)
        except Exception:
            pass

        query = random.choice(query_list)
        
        try:
            print(f"[Trend Agent] Scanning YouTube for AI-generated niche: '{query}'...")
            
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
