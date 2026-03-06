import json
import re
import time
from openai import OpenAI
from config import TOGETHER_API_KEY, TOGETHER_BASE_URL, LLM_MODEL

SCORING_TEMPERATURE = 0.7
SCORING_REASONING = {"enabled": True}


class ScoringAgent:
    """
    Base scoring agent. Subclasses provide system_prompt and score_resume().
    Handles: LLM call, JSON parsing with regex fallback, 3-attempt retry,
    returns 0 on all failures (never raises).
    """

    MAX_RETRIES = 3

    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self._client = OpenAI(
            api_key=TOGETHER_API_KEY,
            base_url=TOGETHER_BASE_URL,
        )

    def _call_llm(self, user_message: str) -> dict:
        """Call LLM and parse JSON response. Returns dict with score/reasoning.
        Uses Qwen3 thinking mode for deeper reasoning and temperature=0.7 for variability.
        Strips <think>...</think> blocks before JSON parsing.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self._client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    max_tokens=4096,
                    temperature=SCORING_TEMPERATURE,
                    extra_body={"reasoning": SCORING_REASONING},
                )
                raw = response.choices[0].message.content or ""
                # Strip Qwen3 thinking blocks before parsing
                raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
                return self._parse_json(raw)
            except Exception:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(1)
        return {"score": 0, "reasoning": "Failed after retries"}

    def _parse_json(self, raw: str) -> dict:
        """Parse JSON from LLM response, with regex fallback."""
        raw = raw.strip()
        # Try direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Try parsing the largest JSON-looking object first.
        first_brace = raw.find("{")
        last_brace = raw.rfind("}")
        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            try:
                return json.loads(raw[first_brace:last_brace + 1])
            except json.JSONDecodeError:
                pass

        # Fall back to parsing any small JSON objects embedded in the response.
        for match in re.finditer(r"\{.*?\}", raw, re.DOTALL):
            try:
                parsed = json.loads(match.group())
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

        # Last resort: extract any score-like fields from partially malformed output.
        scores = {
            key: int(value)
            for key, value in re.findall(r'"(score(?:_[a-zA-Z0-9]+)?)"\s*:\s*(-?\d+)', raw)
        }
        if scores:
            scores["reasoning"] = raw[:200]
            return scores

        return {"score": 0, "reasoning": raw[:200]}
