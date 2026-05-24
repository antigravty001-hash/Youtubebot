import os

# API Keys (loaded from environment variables in GitHub Actions)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

# YouTube Channels Setup (Each needs its own refresh token)
# We will use env variables: YOUTUBE_KIDS_REFRESH_TOKEN, YOUTUBE_FACTS_REFRESH_TOKEN
CHANNELS = {
    "kids": {
        "client_id": os.environ.get("YOUTUBE_CLIENT_ID"),
        "client_secret": os.environ.get("YOUTUBE_CLIENT_SECRET"),
        "refresh_token": os.environ.get("YOUTUBE_KIDS_REFRESH_TOKEN"),
        "category_id": "22", # People & Blogs
        "made_for_kids": True
    },
    "facts": {
        "client_id": os.environ.get("YOUTUBE_CLIENT_ID"),
        "client_secret": os.environ.get("YOUTUBE_CLIENT_SECRET"),
        "refresh_token": os.environ.get("YOUTUBE_FACTS_REFRESH_TOKEN"),
        "category_id": "27", # Education
        "made_for_kids": False
    }
}

# Supported Languages
LANGUAGES = ["en", "tr"]

# Voices for edge-tts
VOICES = {
    "en": {
        "female": "en-US-AriaNeural",
        "male": "en-US-GuyNeural"
    },
    "tr": {
        "female": "tr-TR-EmelNeural",
        "male": "tr-TR-AhmetNeural"
    }
}

# Resolution & Format settings
FORMATS = {
    "shorts": {"width": 1080, "height": 1920, "is_vertical": True},
    "long": {"width": 1920, "height": 1080, "is_vertical": False}
}

# General Prompts / Themes
THEMES = {
    "kids": [
        "A magical forest adventure about sharing.",
        "A little space rover discovering new planets.",
        "Animals learning how to work as a team.",
        "A brave little fox finding its way home."
    ],
    "facts": [
        "Mind-blowing facts about deep space.",
        "Unsolved historical mysteries.",
        "Weirdest animals on Earth.",
        "Hidden secrets of ancient civilizations."
    ]
}
