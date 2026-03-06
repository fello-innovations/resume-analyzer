from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_DRIVE_SCOPES


def get_drive_service():
    """Authenticate with service account and return Drive API client."""
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE,
        scopes=GOOGLE_DRIVE_SCOPES,
    )
    return build("drive", "v3", credentials=creds)
