import io
import pytest
from unittest.mock import patch, MagicMock
from models.schemas import ResumeFile
from parsers.docx_parser import DocxParser


@pytest.fixture
def docx_file():
    return ResumeFile(
        file_id="docx_1",
        name="resume.docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        web_view_link="",
    )


def test_docx_parser_extracts_paragraphs(docx_file):
    mock_doc = MagicMock()
    mock_para1 = MagicMock()
    mock_para1.text = "Jane Smith"
    mock_para2 = MagicMock()
    mock_para2.text = "Software Engineer"
    mock_para3 = MagicMock()
    mock_para3.text = ""  # Empty paragraph — should be filtered
    mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]

    with patch("parsers.docx_parser.Document", return_value=mock_doc):
        parser = DocxParser()
        result = parser.parse(docx_file, b"fake_docx")

    assert "Jane Smith" in result.text
    assert "Software Engineer" in result.text


def test_docx_parser_empty_doc(docx_file):
    mock_doc = MagicMock()
    mock_doc.paragraphs = []

    with patch("parsers.docx_parser.Document", return_value=mock_doc):
        parser = DocxParser()
        result = parser.parse(docx_file, b"fake_docx")

    assert result.text == ""
