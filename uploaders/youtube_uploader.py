import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config.settings import CHANNELS

class YouTubeUploader:
    def __init__(self):
        pass

    def get_service(self, channel_type: str):
        creds_data = CHANNELS[channel_type]
        creds = Credentials(
            token=None,
            refresh_token=creds_data["refresh_token"],
            client_id=creds_data["client_id"],
            client_secret=creds_data["client_secret"],
            token_uri='https://oauth2.googleapis.com/token'
        )
        # Refresh the token
        creds.refresh(Request())
        return build('youtube', 'v3', credentials=creds)

    def upload(self, video_path: str, channel_type: str, title: str, description: str, tags: list):
        if not CHANNELS[channel_type]["refresh_token"]:
            print(f"Skipping upload for {channel_type}: No refresh token provided.")
            return None

        youtube = self.get_service(channel_type)
        body = {
            'snippet': {
                'title': title[:100], # Max 100 chars
                'description': description + "\n\n" + " ".join(f"#{t}" for t in tags),
                'tags': tags,
                'categoryId': CHANNELS[channel_type]["category_id"]
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': CHANNELS[channel_type]["made_for_kids"]
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        try:
            request = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            response = request.execute()
            print(f"✅ Video Uploaded: https://youtube.com/watch?v={response['id']}")
            return response['id']
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return None

    def set_thumbnail(self, video_id: str, thumbnail_path: str, channel_type: str):
        if not CHANNELS[channel_type]["refresh_token"]:
            return False
            
        youtube = self.get_service(channel_type)
        try:
            request = youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            )
            request.execute()
            print(f"✅ Thumbnail Uploaded for Video ID: {video_id}")
            return True
        except Exception as e:
            print(f"❌ Thumbnail upload failed: {e}")
            return False
