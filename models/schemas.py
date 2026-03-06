from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ResumeFile:
    file_id: str
    name: str
    mime_type: str
    web_view_link: str

@dataclass
class ContactInfo:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None

@dataclass
class Scores:
    score_q1: int = 0
    score_q2: int = 0
    score_q3: int = 0
    score_q4: int = 0
    score_q5: int = 0  # JD match score

    @property
    def total(self) -> int:
        return self.score_q1 + self.score_q2 + self.score_q3 + self.score_q4 + self.score_q5

@dataclass
class ParsedResume:
    file: ResumeFile
    text: str
    is_image_based: bool = False
    page_images: list[bytes] = field(default_factory=list)

@dataclass
class ResumeResult:
    file: ResumeFile
    contact: ContactInfo
    scores: Scores
    error: Optional[str] = None
