import os
import random
import time
from loguru import logger


def upload_to_youtube(
    video_path: str,
    title: str,
    description: str = "",
    tags: list = None,
    category: str = "28",
    privacy: str = "private",
    credentials_file: str = "client_secret.json",
    token_file: str = "youtube-oauth2.json",
) -> str:
    """
    Upload a video to YouTube using OAuth2.

    Requires: pip install google-api-python-client google-auth-oauthlib

    Args:
        video_path: Path to the video file
        title: Video title
        description: Video description
        tags: List of tags
        category: YouTube category ID (default "28" = Science & Technology)
        privacy: Privacy status: "private", "unlisted", or "public"
        credentials_file: Path to OAuth2 client secret JSON
        token_file: Path to cached OAuth2 token JSON

    Returns:
        Video URL on success, empty string on failure
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        logger.error(
            "YouTube upload requires: pip install google-api-python-client google-auth-oauthlib"
        )
        return ""

    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return ""

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    # Authenticate
    creds = None
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if not os.path.exists(credentials_file):
            logger.error(
                f"OAuth2 client secret not found: {credentials_file}. "
                "Download it from Google Cloud Console."
            )
            return ""
        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],  # YouTube title max 100 chars
            "description": description[:5000],
            "tags": tags or [],
            "categoryId": category,
        },
        "status": {
            "privacyStatus": privacy,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=256 * 1024,  # 256KB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    # Upload with exponential backoff
    response = None
    max_retries = 10
    retry = 0

    while response is None:
        try:
            logger.info(f"uploading video: {video_path}")
            status, response = request.next_chunk()
            if status:
                logger.info(f"upload progress: {int(status.progress() * 100)}%")
        except Exception as e:
            retry += 1
            if retry > max_retries:
                logger.error(f"YouTube upload failed after {max_retries} retries: {e}")
                return ""
            wait = random.uniform(0, 2 ** retry)
            logger.warning(f"upload error, retrying in {wait:.1f}s: {e}")
            time.sleep(wait)

    if response:
        video_id = response.get("id", "")
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.success(f"YouTube upload completed: {video_url}")
        return video_url

    return ""
