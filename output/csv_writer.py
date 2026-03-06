import csv
import threading
from models.schemas import ResumeResult

CSV_COLUMNS = [
    "name", "email", "phone", "linkedin", "resume_url",
    "score_q1", "score_q2", "score_q3", "score_q4", "score_q5", "total_score", "error",
]


def _make_row(result: ResumeResult) -> dict:
    return {
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
    }


class LiveCsvWriter:
    """Writes each result to CSV immediately as it completes (thread-safe).
    Opens the file in append mode after writing the header once.
    """

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        # Write header on init
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_COLUMNS).writeheader()

    def append(self, result: ResumeResult) -> None:
        with self._lock:
            with open(self.path, "a", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=CSV_COLUMNS).writerow(_make_row(result))


def write_results_to_csv(results: list[ResumeResult], path: str) -> None:
    """Write all results at once, sorted by total_score descending.
    Used for final re-sort after all processing is done.
    """
    sorted_results = sorted(results, key=lambda r: r.scores.total, reverse=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for result in sorted_results:
            writer.writerow(_make_row(result))
