from agents.scoring_agent import ScoringAgent

_STRICT_RUBRIC = """
Scoring rubric - apply strictly:
- 18-20: Exceptional and rare. Direct evidence of strong accomplishments and deep tool fluency.
- 14-17: Strong match, but some gaps remain in depth, scope, recency, or relevance.
-  9-13: Moderate match. Some relevant overlap, but several important signals are weak or missing.
-  4-8 : Weak match. Limited evidence for this criterion.
-  0-3 : Poor fit or clear mismatch.

Strict scoring rules:
- Most candidates should land in the 6-14 range, not 18-20.
- Required tools that are not explicitly shown should be treated as missing.
- Generic claims without scope, outcomes, or depth should not score highly.
- Penalize shallow experience, outdated tools, or adjacent-but-not-direct relevance.
"""

_SYSTEM_TEMPLATE = """You are a strict, critical hiring evaluator scoring resumes for a specific role.
You will reason carefully before scoring, then output your final scores.
Your job is to judge demonstrated evidence, not optimism.

The hiring manager's criteria:
Q3 — Prior experience and accomplishments that signal success:
{q3_answer}

Q4 — Required tools, platforms, and technologies:
{q4_answer}
{strict_rubric}
Score the resume on TWO dimensions (each 0-20):
1. Q3 Score (0-20): How closely does the candidate's experience match the desired signals?
2. Q4 Score (0-20): How well does the candidate demonstrate the required tools and technologies?

Additional instructions:
- Give low scores when the resume lacks concrete accomplishments, scale, ownership, or outcomes.
- Give low scores when required tools are absent, only mentioned casually, or not tied to real work.
- A resume can be strong in one dimension and weak in the other; score each independently.

After your reasoning, respond with valid JSON in this EXACT format:
{{"score_q3": <int 0-20>, "score_q4": <int 0-20>, "reasoning_q3": "<one sentence>", "reasoning_q4": "<one sentence>"}}"""

_USER_TEMPLATE = """Resume to evaluate:
---
{resume_text}
---
Score this resume on Q3 and Q4.
Be strict, skeptical, and conservative.
Penalize heavily for missing required tools, shallow experience, vague claims, or weak accomplishment evidence."""


class Agent2(ScoringAgent):
    def __init__(self, q3_answer: str, q4_answer: str):
        system_prompt = _SYSTEM_TEMPLATE.format(
            q3_answer=q3_answer,
            q4_answer=q4_answer,
            strict_rubric=_STRICT_RUBRIC,
        )
        super().__init__(system_prompt)

    def score_resume(self, resume_text: str) -> tuple[int, int]:
        """Returns (score_q3, score_q4), each 0-20. Never raises."""
        try:
            result = self._call_llm(_USER_TEMPLATE.format(resume_text=resume_text[:8000]))
            q3 = max(0, min(20, int(result.get("score_q3", 0))))
            q4 = max(0, min(20, int(result.get("score_q4", 0))))
            return q3, q4
        except Exception:
            return 0, 0


def create_agent2(q3_answer: str, q4_answer: str) -> Agent2:
    return Agent2(q3_answer, q4_answer)
