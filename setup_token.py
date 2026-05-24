import os
from google_auth_oauthlib.flow import InstalledAppFlow

# You need to download your client_secrets.json from Google Cloud Console
# and place it in the same directory as this script.
CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"Error: {CLIENT_SECRETS_FILE} not found!")
        print("Please download it from Google Cloud Console -> Credentials -> OAuth 2.0 Client IDs")
        return

    print("This script will open a browser window. Please log in with the YouTube channel you want to authorize.")
    print("If you have TWO channels (Kids and Facts), you will need to run this script TWICE, logging into a different channel each time.")
    
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n" + "="*50)
    print("SUCCESS! Here is your REFRESH TOKEN. Save this securely!")
    print("="*50)
    print(creds.refresh_token)
    print("="*50 + "\n")
    print("Copy this value and add it to your GitHub Repository Secrets as either:")
    print("- YOUTUBE_KIDS_REFRESH_TOKEN")
    print("- YOUTUBE_FACTS_REFRESH_TOKEN")

if __name__ == '__main__':
    main()
