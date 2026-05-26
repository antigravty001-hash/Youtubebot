"""
News-Jacker Agent: Scrapes trending news and finds dark historical parallels.
Activated automatically on the 5th video production of each day.
"""
import random
import feedparser

class NewsAgent:
    def __init__(self):
        # Google News RSS feeds (free, no API key needed)
        self.feeds = {
            "tr": [
                "https://news.google.com/rss?hl=tr&gl=TR&ceid=TR:tr",
                "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FuUnlHZ0pVVWlnQVAB?hl=tr&gl=TR&ceid=TR:tr",  # Science/Tech
            ],
            "en": [
                "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",  # Science/Tech
            ]
        }

    def get_trending_news(self, language: str) -> list:
        """Fetches top trending news headlines from Google News RSS."""
        feed_urls = self.feeds.get(language, self.feeds["en"])
        headlines = []

        for url in feed_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:10]:
                    title = entry.get("title", "")
                    if title:
                        # Remove source suffix like " - BBC News"
                        clean_title = title.split(" - ")[0].strip() if " - " in title else title
                        headlines.append(clean_title)
            except Exception as e:
                print(f"[News Agent] Failed to parse feed: {e}")
                continue

        return headlines

    def get_news_topic(self, language: str) -> str:
        """
        Fetches trending news and constructs a dark-history-parallel topic.
        Returns a topic string that the WriterAgent can use.
        """
        print("[News Agent] 📰 Scanning breaking news for dark history parallels...")
        headlines = self.get_trending_news(language)

        if not headlines:
            print("[News Agent] ⚠️ No headlines found. Falling back to standard topic.")
            return None

        # Pick 3 random headlines from top stories to give Gemini variety
        selected = random.sample(headlines[:15], min(3, len(headlines)))
        
        news_summary = " | ".join(selected)
        print(f"[News Agent] 🎯 Top headlines: {news_summary}")

        # Build the topic instruction for the WriterAgent
        topic = (
            f"NEWS-JACKER MODE: Today's biggest news headlines are: [{news_summary}]. "
            f"Your mission: Find the DARKEST, most TERRIFYING historical parallel to one of these "
            f"modern events. The video must feel like 'history is repeating itself' and expose a "
            f"chilling connection between past and present. Make viewers feel like they are watching "
            f"a classified documentary that reveals a pattern the public was never supposed to see."
        )

        return topic
