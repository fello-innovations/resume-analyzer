import csv
from models.schemas import ResumeResult

CSV_COLUMNS = [
    "name", "email", "phone", "linkedin", "resume_url",
    "score_q1", "score_q2", "score_q3", "score_q4", "score_q5", "total_score", "error",
]


def write_results_to_csv(results: list[ResumeResult], path: str) -> None:
    """Write ranked resume results to a CSV file, sorted by total_score descending."""
    sorted_results = sorted(
        results,
        key=lambda r: r.scores.total,
        reverse=True,
    )

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for result in sorted_results:
            writer.writerow({
                "name": result.contact.name or "",
                "email": result.contact.email or "",
                "phone": result.contact.phone or "",
                "linkedin": result.contact.linkedin or "",
                "resume_url": result.file.web_view_link,
                "score_q1": result.scores.score_q1,
                "score_q2": result.scores.score_q2,
                "score_q3": result.scores.score_q3,
                "score_q4": result.scores.score_q4,
                "score_q5": result.scores.score_q5,
                "total_score": result.scores.total,
                "error": result.error or "",
            })
