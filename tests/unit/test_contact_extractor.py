import pytest
from unittest.mock import patch, MagicMock
from agents.contact_extractor import ContactExtractor


RESUME_TEXT = """
John Doe
john.doe@company.com
+1-555-987-6543
https://linkedin.com/in/johndoe
Senior Software Engineer with 8 years of experience.
"""


def make_mock_llm_response(content: str):
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    return mock_resp


def test_contact_extractor_regex_email():
    with patch("agents.contact_extractor.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value = make_mock_llm_response(
            '{"name": "John Doe", "email": null, "phone": null, "linkedin": null}'
        )
        extractor = ContactExtractor()
        result = extractor.extract(RESUME_TEXT)

    assert result.email == "john.doe@company.com"


def test_contact_extractor_regex_phone():
    with patch("agents.contact_extractor.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value = make_mock_llm_response(
            '{"name": "John Doe", "email": null, "phone": null, "linkedin": null}'
        )
        extractor = ContactExtractor()
        result = extractor.extract(RESUME_TEXT)

    assert "555" in result.phone


def test_contact_extractor_llm_name():
    with patch("agents.contact_extractor.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value = make_mock_llm_response(
            '{"name": "John Doe", "email": null, "phone": null, "linkedin": null}'
        )
        extractor = ContactExtractor()
        result = extractor.extract(RESUME_TEXT)

    assert result.name == "John Doe"


def test_contact_extractor_llm_failure_returns_partial():
    with patch("agents.contact_extractor.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = Exception("API down")
        extractor = ContactExtractor()
        result = extractor.extract(RESUME_TEXT)

    # Regex fields still extracted
    assert result.email == "john.doe@company.com"
    assert result.name is None  # LLM failed
