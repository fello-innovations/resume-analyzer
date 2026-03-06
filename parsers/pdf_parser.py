import io
from typing import Optional
import pdfplumber
from models.schemas import ParsedResume, ResumeFile
from parsers.base_parser import BaseParser
from config import IMAGE_TEXT_THRESHOLD


class PDFParser(BaseParser):
    """
    Parses PDF files.
    - Attempts text extraction via pdfplumber.
    - If average chars/page < IMAGE_TEXT_THRESHOLD, flags as image-based
      and populates page_images (PNG bytes) via pdf2image for vision LLM.
    """

    def parse(self, file: ResumeFile, content: bytes) -> ParsedResume:
        text, avg_chars = self._extract_text(content)

        if avg_chars < IMAGE_TEXT_THRESHOLD:
            page_images = self._render_pages(content)
            return ParsedResume(
                file=file,
                text=text,
                is_image_based=True,
                page_images=page_images,
            )

        return ParsedResume(file=file, text=text)

    def _extract_text(self, content: bytes) -> tuple[str, float]:
        pages_text = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text() or ""
                pages_text.append(extracted)

        full_text = "\n".join(pages_text).strip()
        num_pages = len(pages_text) or 1
        avg_chars = len(full_text) / num_pages
        return full_text, avg_chars

    def _render_pages(self, content: bytes) -> list[bytes]:
        """Render PDF pages to PNG bytes using pdf2image."""
        try:
            from pdf2image import convert_from_bytes
            import io as _io
            images = convert_from_bytes(content, fmt="png")
            result = []
            for img in images:
                buf = _io.BytesIO()
                img.save(buf, format="PNG")
                result.append(buf.getvalue())
            return result
        except Exception:
            return []
