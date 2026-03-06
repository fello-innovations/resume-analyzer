"""
Integration test: full pipeline with mocked Drive service and LLM calls.
Validates end-to-end data flow without making real API calls.
"""
import pytest
from unittest.mock import MagicMock, patch
from models.schemas import ResumeFile, ContactInfo, Scores, ParsedResume
from agents.agent1 import Agent1
from agents.agent2 import Agent2
from agents.agent3 import Agent3
from agents.contact_extractor import ContactExtractor
from parsers.image_parser import ImageParser
from output.csv_writer import write_results_to_csv
import tempfile, csv, os


SAMPLE_RESUME_TEXT = """
Alice Johnson
alice@example.com
+1-650-555-9999
linkedin.com/in/alicejohnson

Senior Python Engineer | 7 years experience
Startups: TechCo (Series A), BuildIt (seed)
Skills: Python, Django, PostgreSQL, Docker, AWS
"""

SAMPLE_JD = "Senior Software Engineer — Python, AWS, Docker, startup experience required."


def make_llm_response(content: str):
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    return mock_resp


@pytest.fixture
def mock_drive_service():
    service = MagicMock()
    service.files.return_value.list.return_value.execute.return_value = {
        "files": [
            {
                "id": "resume_1",
                "name": "alice_resume.pdf",
                "mimeType": "application/pdf",
                "webViewLink": "https://drive.google.com/file/d/resume_1/view",
            }
        ]
    }
    return service


def test_full_pipeline_single_resume(mock_drive_service):
    """End-to-end test: parse -> score (5 dimensions) -> contact -> CSV."""
    resume_file = ResumeFile(
        file_id="resume_1",
        name="alice_resume.pdf",
        mime_type="application/pdf",
        web_view_link="https://drive.google.com/file/d/resume_1/view",
    )

    with patch("agents.scoring_agent.OpenAI") as MockLLM, \
         patch("agents.contact_extractor.OpenAI") as MockContactLLM, \
         patch("parsers.pdf_parser.pdfplumber") as mock_plumber:

        # Mock PDF parsing
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_RESUME_TEXT
        mock_pdf.pages = [mock_page]
        mock_plumber.open.return_value.__enter__.return_value = mock_pdf

        # Mock scoring LLM — 3 calls: agent1, agent2, agent3
        MockLLM.return_value.chat.completions.create.side_effect = [
            make_llm_response('{"score_q1": 17, "score_q2": 18, "reasoning_q1": "good match", "reasoning_q2": "no deal breakers"}'),
            make_llm_response('{"score_q3": 15, "score_q4": 16, "reasoning_q3": "startup exp", "reasoning_q4": "has tools"}'),
            make_llm_response('{"score_q5": 14, "reasoning_q5": "strong JD match"}'),
        ]

        # Mock contact LLM
        MockContactLLM.return_value.chat.completions.create.return_value = make_llm_response(
            '{"name": "Alice Johnson", "email": null, "phone": null, "linkedin": null}'
        )

        from parsers.pdf_parser import PDFParser
        parser = PDFParser()
        parsed = parser.parse(resume_file, b"fake_pdf")

        agent1 = Agent1("5+ years Python, startup", "no job hopping")
        agent2 = Agent2("startup experience", "Python, Docker, AWS")
        agent3 = Agent3(SAMPLE_JD)
        extractor = ContactExtractor()

        q1, q2 = agent1.score_resume(parsed.text)
        q3, q4 = agent2.score_resume(parsed.text)
        q5 = agent3.score_resume(parsed.text)
        contact = extractor.extract(parsed.text)

    assert q1 == 17
    assert q2 == 18
    assert q3 == 15
    assert q4 == 16
    assert q5 == 14
    assert contact.name == "Alice Johnson"
    assert contact.email == "alice@example.com"
    assert q1 + q2 + q3 + q4 + q5 == 80


def test_agent3_score_resume():
    """Agent3 returns a single int score (0-20) for JD match."""
    with patch("agents.scoring_agent.OpenAI"), \
         patch("agents.agent3.ScoringAgent._call_llm") as mock_call:
        mock_call.return_value = {"score_q5": 13, "reasoning_q5": "moderate fit"}
        agent = Agent3("Python senior engineer role")
        q5 = agent.score_resume("resume text")
    assert q5 == 13


def test_agent3_clamps_to_range():
    """Agent3 clamps out-of-range LLM responses to 0-20."""
    with patch("agents.scoring_agent.OpenAI"), \
         patch("agents.agent3.ScoringAgent._call_llm") as mock_call:
        mock_call.return_value = {"score_q5": 99}
        agent = Agent3("any JD")
        q5 = agent.score_resume("resume text")
    assert q5 == 20


def test_scores_total_includes_q5():
    """Scores.total sums all 5 dimensions."""
    s = Scores(score_q1=18, score_q2=16, score_q3=14, score_q4=17, score_q5=15)
    assert s.total == 80
