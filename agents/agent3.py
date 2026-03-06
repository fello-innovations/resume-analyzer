from agents.scoring_agent import ScoringAgent

_STRICT_RUBRIC = """
Scoring rubric - apply strictly:
- 18-20: Near-perfect JD match. Rare. Candidate clearly matches the role's core requirements, level, and scope.
- 14-17: Strong JD match, but with some smaller gaps.
-  9-13: Partial or mixed JD match. Meets some important requirements but misses others.
-  4-8 : Weak JD match. Only limited overlap with the JD.
-  0-3 : Poor JD match. Misses the role's essential requirements.

Strict scoring rules:
- Most candidates should land in the 6-14 range, not 18-20.
- Missing required qualifications must materially lower the score.
- Missing evidence counts as missing; do not infer skills or experience.
- If seniority, domain, or must-have skills do not align, score aggressively lower.
- Reserve 18+ for candidates who look unusually well matched to this exact JD.
"""

_SYSTEM_TEMPLATE = """You are a strict resume-to-job-description match evaluator.
Your job is to assess how well a candidate's resume aligns with a specific job description.
You will reason carefully through the match before scoring.

Job Description:
---
{jd}
---
{strict_rubric}
Score the resume on ONE dimension (0-20):
- Q5 Score (0-20): Overall match between this candidate's resume and the job description above.
  Consider: required qualifications met, experience level, industry/domain fit, key skills present,
  and any disqualifying gaps.

Additional instructions:
- Focus first on required qualifications, not nice-to-haves.
- Penalize missing seniority, missing must-have tools, or lack of direct domain relevance.
- Do not reward transferable potential if the JD asks for direct evidence.

After your reasoning, respond with valid JSON in this EXACT format:
{{"score_q5": <int 0-20>, "reasoning_q5": "<one sentence summary of match quality>"}}"""

_USER_TEMPLATE = """Resume to evaluate against the job description:
---
{resume_text}
---
Score this resume on Q5 (JD match).
Be strict, skeptical, and conservative.
If key required qualifications are missing, penalize heavily.
If the candidate looks only adjacent to the JD, score lower."""


class Agent3(ScoringAgent):
    def __init__(self, jd: str):
        self.jd = jd.strip()
        system_prompt = _SYSTEM_TEMPLATE.format(
            jd=self.jd or "No job description provided.",
            strict_rubric=_STRICT_RUBRIC,
        )
        super().__init__(system_prompt)

    def score_resume(self, resume_text: str) -> int:
        """Returns score_q5 (0-20). Never raises."""
        if not self.jd:
            return 0
        try:
            result = self._call_llm(_USER_TEMPLATE.format(resume_text=resume_text[:8000]))
            q5 = max(0, min(20, int(result.get("score_q5", 0))))
            return q5
        except Exception:
            return 0


def create_agent3(jd: str) -> Agent3:
    return Agent3(jd)
