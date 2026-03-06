import re
import json
from openai import OpenAI
from models.schemas import ContactInfo
from config import TOGETHER_API_KEY, TOGETHER_BASE_URL, LLM_MODEL

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}"
)
_LINKEDIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+"
)

_SYSTEM_PROMPT = """Extract contact information from this resume text.
Respond ONLY with valid JSON:
{"name": "<full name or null>", "email": "<email or null>", "phone": "<phone or null>", "linkedin": "<linkedin url or null>"}
If a field is not found, use null."""


class ContactExtractor:
    def __init__(self):
        self._client = OpenAI(
            api_key=TOGETHER_API_KEY,
            base_url=TOGETHER_BASE_URL,
        )

    def extract(self, resume_text: str) -> ContactInfo:
        """Hybrid extraction: regex for structured fields, LLM for name + fallback."""
        # Regex pass
        email_match = _EMAIL_RE.search(resume_text)
        phone_match = _PHONE_RE.search(resume_text)
        linkedin_match = _LINKEDIN_RE.search(resume_text)

        email = email_match.group() if email_match else None
        phone = phone_match.group() if phone_match else None
        linkedin = linkedin_match.group() if linkedin_match else None

        # LLM pass for name and any missing fields
        llm_result = self._llm_extract(resume_text[:3000])

        return ContactInfo(
            name=llm_result.get("name"),
            email=email or llm_result.get("email"),
            phone=phone or llm_result.get("phone"),
            linkedin=linkedin or llm_result.get("linkedin"),
        )

    def _llm_extract(self, text: str) -> dict:
        try:
            response = self._client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                max_tokens=256,
                temperature=0.0,
                extra_body={"reasoning": {"enabled": False}},  # disable Qwen3 thinking mode
            )
            raw = response.choices[0].message.content or "{}"
            # Try parse
            try:
                return json.loads(raw.strip())
            except json.JSONDecodeError:
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except Exception:
            pass
        return {}
