from models.schemas import ParsedResume, ResumeFile
from parsers.base_parser import BaseParser


class GDocParser(BaseParser):
    """Parses Google Docs exported as plain text (UTF-8 bytes)."""

    def parse(self, file: ResumeFile, content: bytes) -> ParsedResume:
        text = content.decode("utf-8", errors="replace").strip()
        return ParsedResume(file=file, text=text)
