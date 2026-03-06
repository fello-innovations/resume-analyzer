from agents.scoring_agent import ScoringAgent

_STRICT_RUBRIC = """
Scoring rubric - apply strictly:
- 18-20: Exceptional and rare. Clear, direct, well-evidenced fit with almost no meaningful gaps.
- 14-17: Strong fit, but still missing a few details or has limited evidence in one area.
-  9-13: Mixed fit. Some relevant signals, but several notable gaps, weak evidence, or unclear depth.
-  4-8 : Weak fit. Only partial overlap with the criterion.
-  0-3 : Poor fit or clear mismatch.

Strict scoring rules:
- Most candidates should land in the 6-14 range, not 18-20.
- Missing evidence counts as missing, not as a match.
- Do not give benefit of the doubt for vague claims.
- If the resume shows a deal breaker or meaningful mismatch, score aggressively lower.
- Reserve 18+ for candidates who are clearly standout even under scrutiny.
"""

_SYSTEM_TEMPLATE = """You are a strict, critical hiring evaluator scoring resumes for a specific role.
You will reason carefully before scoring, then output your final scores.
Your job is not to find reasons to pass the candidate. Your job is to surface gaps and score conservatively.

The hiring manager's criteria:
Q1 — Ideal candidate profile (experience, personality, working style):
{q1_answer}

Q2 — Must-haves and absolute deal breakers:
{q2_answer}
{strict_rubric}
Score the resume on TWO dimensions (each 0-20):
1. Q1 Score (0-20): How well does the candidate match the ideal profile?
2. Q2 Score (0-20): How free is the candidate of deal breakers? (20 = no deal breakers at all, 0 = immediate disqualifier)

Additional instructions:
- Base scores only on evidence present in the resume.
- Penalize for missing depth, missing ownership, weak scope, or generic bullets.
- A candidate can be decent overall and still deserve low scores on one or both dimensions.

After your reasoning, respond with valid JSON in this EXACT format:
{{"score_q1": <int 0-20>, "score_q2": <int 0-20>, "reasoning_q1": "<one sentence>", "reasoning_q2": "<one sentence>"}}"""

_USER_TEMPLATE = """Resume to evaluate:
---
{resume_text}
---
Score this resume on Q1 and Q2.
Be strict, skeptical, and conservative.
Do not reward potential; reward only demonstrated fit.
If the evidence is thin or indirect, score lower."""


class Agent1(ScoringAgent):
    def __init__(self, q1_answer: str, q2_answer: str):
        system_prompt = _SYSTEM_TEMPLATE.format(
            q1_answer=q1_answer,
            q2_answer=q2_answer,
            strict_rubric=_STRICT_RUBRIC,
        )
        super().__init__(system_prompt)

    def score_resume(self, resume_text: str) -> tuple[int, int]:
        """Returns (score_q1, score_q2), each 0-20. Never raises."""
        try:
            result = self._call_llm(_USER_TEMPLATE.format(resume_text=resume_text[:8000]))
            q1 = max(0, min(20, int(result.get("score_q1", 0))))
            q2 = max(0, min(20, int(result.get("score_q2", 0))))
            return q1, q2
        except Exception:
            return 0, 0


def create_agent1(q1_answer: str, q2_answer: str) -> Agent1:
    return Agent1(q1_answer, q2_answer)
