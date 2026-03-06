from abc import ABC, abstractmethod
from models.schemas import ParsedResume, ResumeFile


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file: ResumeFile, content: bytes) -> ParsedResume:
        """Parse raw file bytes into a ParsedResume."""
        ...
