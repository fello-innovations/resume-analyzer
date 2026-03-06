#!/usr/bin/env python3
"""
Resume Analyzer — main entry point.

Usage:
    python main.py <google_drive_folder_id>
"""
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import MAX_WORKERS_OUTER, OUTPUT_CSV
from gdrive.auth import get_drive_service
from gdrive.fetcher import list_resume_files, download_file
from parsers import get_parser
from parsers.image_parser import ImageParser
from agents.agent1 import create_agent1
from agents.agent2 import create_agent2
from agents.agent3 import create_agent3
from agents.contact_extractor import ContactExtractor
from models.schemas import ResumeResult, ContactInfo, Scores
from output.csv_writer import LiveCsvWriter, write_results_to_csv


QUESTIONS = [
    ("Q1", "Describe your ideal candidate profile (experience, background, personality):"),
    ("Q2", "What are your absolute deal breakers for this role?"),
    ("Q3", "What prior experience signals would excite you most?"),
    ("Q4", "What specific tools, technologies, or skills are required?"),
    ("JD", "Paste the full Job Description for JD-match scoring (or press Enter to skip Q5):"),
]


def collect_manager_criteria() -> dict[str, str]:
    """Prompt the hiring manager for five scoring inputs."""
    print("\n=== Resume Analyzer: Hiring Manager Setup ===\n")
    print("Please answer the following questions to configure your scoring rubric.")
    print("Each resume will be scored across 5 dimensions worth 20 points each.")
    print("If you skip the JD, Q5 will be 0 and the total will reflect the remaining criteria.\n")
    answers = {}
    for key, question in QUESTIONS:
        print(f"{question}")
        answer = input("> ").strip()
        answers[key] = answer
        print()
    return answers


def process_single_resume(
    resume_file,
    agent1,
    agent2,
    agent3,
    contact_extractor: ContactExtractor,
    image_parser: ImageParser,
) -> ResumeResult:
    """Download, parse, and score a single resume. Never raises.
    Builds its own Drive service to avoid httplib2 thread-safety issues.
    """
    try:
        # Each thread gets its own service client (httplib2 is not thread-safe)
        service = get_drive_service()
        content = download_file(service, resume_file)

        # Parse
        parser = get_parser(resume_file.mime_type)
        parsed = parser.parse(resume_file, content)

        # Image PDF fallback
        if parsed.is_image_based and parsed.page_images:
            parsed.text = image_parser.extract_text_from_images(parsed.page_images)

        resume_text = parsed.text

        # Score + extract contact in parallel (4 threads)
        with ThreadPoolExecutor(max_workers=4) as inner_pool:
            f_agent1 = inner_pool.submit(agent1.score_resume, resume_text)
            f_agent2 = inner_pool.submit(agent2.score_resume, resume_text)
            f_agent3 = inner_pool.submit(agent3.score_resume, resume_text)
            f_contact = inner_pool.submit(contact_extractor.extract, resume_text)

            scores_q1_q2 = f_agent1.result()
            scores_q3_q4 = f_agent2.result()
            score_q5   = f_agent3.result()
            contact    = f_contact.result()

        scores = Scores(
            score_q1=scores_q1_q2[0],
            score_q2=scores_q1_q2[1],
            score_q3=scores_q3_q4[0],
            score_q4=scores_q3_q4[1],
            score_q5=score_q5,
        )

        return ResumeResult(file=resume_file, contact=contact, scores=scores)

    except Exception as e:
        return ResumeResult(
            file=resume_file,
            contact=ContactInfo(),
            scores=Scores(),
            error=str(e),
        )


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <google_drive_folder_id>")
        sys.exit(1)

    folder_id = sys.argv[1]

    # Collect hiring manager criteria
    criteria = collect_manager_criteria()

    print("Authenticating with Google Drive...")
    service = get_drive_service()

    print(f"Listing resumes in folder: {folder_id}")
    resume_files = list_resume_files(service, folder_id)
    print(f"Found {len(resume_files)} resume(s).\n")

    if not resume_files:
        print("No resumes found. Exiting.")
        sys.exit(0)

    # Initialize shared agents and extractors
    agent1 = create_agent1(criteria["Q1"], criteria["Q2"])
    agent2 = create_agent2(criteria["Q3"], criteria["Q4"])
    agent3 = create_agent3(criteria.get("JD", ""))
    contact_extractor = ContactExtractor()
    image_parser = ImageParser()

    results = []
    live_csv = LiveCsvWriter(OUTPUT_CSV)
    print(f"Processing {len(resume_files)} resumes (max {MAX_WORKERS_OUTER} parallel)...\n")
    print(f"Results streaming to: {OUTPUT_CSV}\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS_OUTER) as outer_pool:
        futures = {
            outer_pool.submit(
                process_single_resume,
                rf, agent1, agent2, agent3, contact_extractor, image_parser,
            ): rf
            for rf in resume_files
        }
        for i, future in enumerate(as_completed(futures), 1):
            rf = futures[future]
            result = future.result()
            live_csv.append(result)
            results.append(result)
            status = f"ERROR: {result.error}" if result.error else f"score={result.scores.total}"
            print(f"[{i}/{len(resume_files)}] {rf.name} — {status}")

    # Re-write sorted by score at the end
    write_results_to_csv(results, OUTPUT_CSV)
    print(f"\nDone! Results sorted and written to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
