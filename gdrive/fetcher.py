import io
from typing import Generator
from googleapiclient.http import MediaIoBaseDownload
from models.schemas import ResumeFile

RESUME_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/vnd.google-apps.document",
}


def list_resume_files(service, folder_id: str) -> list[ResumeFile]:
    """List all resume files in a Drive folder (paginated)."""
    files = []
    page_token = None
    query = f"'{folder_id}' in parents and trashed=false"

    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType, webViewLink)",
            pageToken=page_token,
            pageSize=100,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

        for f in response.get("files", []):
            if f["mimeType"] in RESUME_MIME_TYPES:
                files.append(ResumeFile(
                    file_id=f["id"],
                    name=f["name"],
                    mime_type=f["mimeType"],
                    web_view_link=f.get("webViewLink", ""),
                ))

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return files


def download_file(service, resume_file: ResumeFile) -> bytes:
    """Download a Drive file, exporting Google Docs as plain text."""
    if resume_file.mime_type == "application/vnd.google-apps.document":
        request = service.files().export_media(
            fileId=resume_file.file_id,
            mimeType="text/plain",
        )
    else:
        request = service.files().get_media(fileId=resume_file.file_id)

    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()
