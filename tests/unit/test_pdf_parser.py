import pytest
from unittest.mock import patch, MagicMock
from models.schemas import ResumeFile
from parsers.pdf_parser import PDFParser


@pytest.fixture
def pdf_file():
    return ResumeFile(
        file_id="pdf_1",
        name="resume.pdf",
        mime_type="application/pdf",
        web_view_link="",
    )


def test_pdf_parser_text_extraction(pdf_file):
    """PDF with sufficient text returns ParsedResume with is_image_based=False."""
    mock_text = "A" * 200  # Well above threshold
    with patch("parsers.pdf_parser.pdfplumber") as mock_plumber:
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = mock_text
        mock_pdf.pages = [mock_page]
        mock_plumber.open.return_value.__enter__.return_value = mock_pdf

        parser = PDFParser()
        result = parser.parse(pdf_file, b"fake_pdf_bytes")

    assert result.is_image_based is False
    assert result.text == mock_text


def test_pdf_parser_image_based_detection(pdf_file):
    """PDF with sparse text is flagged as image-based."""
    with patch("parsers.pdf_parser.pdfplumber") as mock_plumber:
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "AB"  # Very short — below threshold
        mock_pdf.pages = [mock_page]
        mock_plumber.open.return_value.__enter__.return_value = mock_pdf

        with patch.object(PDFParser, "_render_pages", return_value=[b"png_bytes"]):
            parser = PDFParser()
            result = parser.parse(pdf_file, b"fake_pdf_bytes")

    assert result.is_image_based is True
    assert result.page_images == [b"png_bytes"]
