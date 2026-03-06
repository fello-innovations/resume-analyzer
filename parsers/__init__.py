from models.schemas import ResumeFile
from parsers.gdoc_parser import GDocParser
from parsers.docx_parser import DocxParser
from parsers.pdf_parser import PDFParser


def get_parser(mime_type: str):
    """Return the appropriate parser for a given MIME type."""
    if mime_type == "application/vnd.google-apps.document":
        return GDocParser()
    elif mime_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        return DocxParser()
    elif mime_type == "application/pdf":
        return PDFParser()
    else:
        raise ValueError(f"Unsupported MIME type: {mime_type}")
