import pytest
from models.schemas import ResumeFile, ContactInfo, Scores, ParsedResume, ResumeResult


@pytest.fixture
def sample_resume_file():
    return ResumeFile(
        file_id="file_123",
        name="john_doe_resume.pdf",
        mime_type="application/pdf",
        web_view_link="https://drive.google.com/file/d/file_123/view",
    )


@pytest.fixture
def sample_parsed_resume(sample_resume_file):
    return ParsedResume(
        file=sample_resume_file,
        text="John Doe\njohn@example.com\n+1-555-123-4567\nlinkedin.com/in/johndoe\n5 years Python experience at startups.",
    )


@pytest.fixture
def sample_contact():
    return ContactInfo(
        name="John Doe",
        email="john@example.com",
        phone="+1-555-123-4567",
        linkedin="linkedin.com/in/johndoe",
    )


@pytest.fixture
def sample_scores():
    return Scores(score_q1=20, score_q2=18, score_q3=22, score_q4=19)


@pytest.fixture
def sample_result(sample_resume_file, sample_contact, sample_scores):
    return ResumeResult(
        file=sample_resume_file,
        contact=sample_contact,
        scores=sample_scores,
    )
