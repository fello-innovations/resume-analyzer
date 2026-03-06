import pytest
from unittest.mock import MagicMock, patch
from models.schemas import ResumeFile
from gdrive.fetcher import list_resume_files, download_file


def make_drive_service(files_data, next_page_token=None):
    """Helper to create a mock Drive service."""
    mock_service = MagicMock()
    response = {"files": files_data}
    if next_page_token:
        response["nextPageToken"] = next_page_token
    mock_service.files.return_value.list.return_value.execute.return_value = response
    return mock_service


def test_list_resume_files_filters_mime_types():
    files_data = [
        {"id": "1", "name": "resume.pdf", "mimeType": "application/pdf", "webViewLink": "url1"},
        {"id": "2", "name": "image.png", "mimeType": "image/png", "webViewLink": "url2"},  # filtered out
        {"id": "3", "name": "resume.docx", "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "webViewLink": "url3"},
    ]
    service = make_drive_service(files_data)
    results = list_resume_files(service, "folder_id")

    assert len(results) == 2
    assert all(isinstance(r, ResumeFile) for r in results)
    names = [r.name for r in results]
    assert "resume.pdf" in names
    assert "image.png" not in names


def test_download_file_regular():
    service = MagicMock()
    resume_file = ResumeFile(
        file_id="file_1", name="resume.pdf",
        mime_type="application/pdf", web_view_link=""
    )

    with patch("gdrive.fetcher.MediaIoBaseDownload") as MockDownloader:
        mock_dl = MagicMock()
        mock_dl.next_chunk.return_value = (None, True)
        MockDownloader.return_value = mock_dl
        download_file(service, resume_file)

    service.files.return_value.get_media.assert_called_once_with(fileId="file_1")


def test_download_file_gdoc_exports_as_text():
    service = MagicMock()
    resume_file = ResumeFile(
        file_id="doc_1", name="My Resume",
        mime_type="application/vnd.google-apps.document", web_view_link=""
    )

    with patch("gdrive.fetcher.MediaIoBaseDownload") as MockDownloader:
        mock_dl = MagicMock()
        mock_dl.next_chunk.return_value = (None, True)
        MockDownloader.return_value = mock_dl
        download_file(service, resume_file)

    service.files.return_value.export_media.assert_called_once_with(
        fileId="doc_1", mimeType="text/plain"
    )
