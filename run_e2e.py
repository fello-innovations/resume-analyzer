#!/usr/bin/env python3
"""
End-to-end test runner with pre-filled manager criteria.
No interactive prompts — runs the full pipeline automatically.

Usage:
    python run_e2e.py
    python run_e2e.py --folder <folder_id> --output custom_results.csv
"""
import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
load_dotenv()
load_dotenv(".env.local", override=True)

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("e2e_run.log"),
    ],
)
log = logging.getLogger(__name__)

# ─── Manager Criteria (pre-filled for E2E testing) ──────────────────────────
# These represent a typical Senior Software Engineer hiring bar.
# In production these come from the CLI prompts in main.py.

CRITERIA = {
    "Q1": (
        "The ideal Head of Finance candidate has 8+ years of progressive finance experience, "
        "with at least 3 years in a senior or leadership role. They are highly analytical, "
        "strategic, and able to translate complex financial data into business decisions. "
        "They are a strong communicator who can partner with the CEO and board, build a "
        "finance team from the ground up, and thrive in a fast-paced startup or scale-up "
        "environment. They take full ownership of the finance function."
    ),
    "Q2": (
        "Deal breakers: no experience owning a full P&L or financial reporting function, "
        "no exposure to fundraising or investor relations, purely operational accounting "
        "background without any strategic finance experience, evidence of frequent "
        "job-hopping (more than 4 companies in 5 years), or never worked in a growth-stage "
        "or venture-backed company."
    ),
    "Q3": (
        "Strong signals: led a Series A or later fundraising process, built a finance "
        "function from scratch at a startup, implemented financial systems or ERP tools, "
        "managed audit and compliance end-to-end, experience with board reporting and "
        "investor updates, previously held CFO or VP Finance title at a company with "
        "$10M+ ARR, or played a key role in an M&A or acquisition process."
    ),
    "Q4": (
        "Required: strong Excel/Google Sheets financial modeling, experience with at least "
        "one ERP or accounting system (NetSuite, QuickBooks, Xero, or similar), familiarity "
        "with GAAP accounting standards. Nice-to-have: experience with Carta for cap table "
        "management, data visualization tools (Looker, Tableau), SQL for financial analysis, "
        "or experience with SaaS metrics and recurring revenue models."
    ),
    "JD": (
        "Head of Finance — Full-Time | Series B SaaS Company | San Francisco, CA\n\n"
        "About the Role:\n"
        "We are a fast-growing B2B SaaS company (Series B, $40M ARR) seeking a Head of Finance "
        "to own the finance function end-to-end. You will report directly to the CEO and work "
        "closely with the board. This is a high-impact, hands-on role for a strategic finance "
        "leader who is equally comfortable building financial models and presenting to investors.\n\n"
        "Responsibilities:\n"
        "- Own financial planning & analysis (FP&A), budgeting, and forecasting\n"
        "- Lead the next fundraising round (Series C target: $80M)\n"
        "- Manage audit, tax compliance, and GAAP financial reporting\n"
        "- Build and scale the finance team (currently 2 FTEs)\n"
        "- Own the cap table and work with Carta for equity management\n"
        "- Partner with Sales and Customer Success on revenue recognition and SaaS metrics\n"
        "- Prepare board-level financial reporting and investor updates\n\n"
        "Requirements:\n"
        "- 8+ years of progressive finance experience, with 3+ years in a senior finance leadership role\n"
        "- Experience at a venture-backed startup ($10M–$100M ARR preferred)\n"
        "- Proven track record in fundraising (Series A or later) or M&A\n"
        "- CPA or MBA strongly preferred\n"
        "- Proficiency in NetSuite or similar ERP, Excel/Google Sheets modeling\n"
        "- Deep understanding of SaaS metrics (ARR, NRR, CAC, LTV, churn)\n"
        "- Experience managing an audit process end-to-end\n\n"
        "Nice to Have:\n"
        "- Carta experience for cap table management\n"
        "- SQL or data visualization skills (Looker, Tableau)\n"
        "- Prior CFO experience at a startup\n"
    ),
}

FOLDER_ID = "1TXQSGyUFcK8xpU_7lPkG8qXlvIMHp_bl"


def process_single_resume(resume_file, agent1, agent2, agent3, contact_extractor, image_parser):
    """Full pipeline for one resume. Never raises.
    Each call builds its own Drive service to avoid httplib2 thread-safety issues.
    """
    try:
        # Build a fresh service per thread — httplib2 is not thread-safe
        service = get_drive_service()
        content = download_file(service, resume_file)
        parser = get_parser(resume_file.mime_type)
        parsed = parser.parse(resume_file, content)

        if parsed.is_image_based and parsed.page_images:
            log.info(f"  [OCR] Image-based PDF: {resume_file.name}")
            parsed.text = image_parser.extract_text_from_images(parsed.page_images)

        resume_text = parsed.text
        if not resume_text.strip():
            log.warning(f"  [WARN] Empty text for {resume_file.name}")

        with ThreadPoolExecutor(max_workers=4) as pool:
            f1 = pool.submit(agent1.score_resume, resume_text)
            f2 = pool.submit(agent2.score_resume, resume_text)
            f3 = pool.submit(agent3.score_resume, resume_text)
            fc = pool.submit(contact_extractor.extract, resume_text)
            q1, q2 = f1.result()
            q3, q4 = f2.result()
            q5     = f3.result()
            contact = fc.result()

        return ResumeResult(
            file=resume_file,
            contact=contact,
            scores=Scores(score_q1=q1, score_q2=q2, score_q3=q3, score_q4=q4, score_q5=q5),
        )
    except Exception as e:
        log.error(f"  [ERROR] {resume_file.name}: {e}", exc_info=True)
        return ResumeResult(
            file=resume_file,
            contact=ContactInfo(),
            scores=Scores(),
            error=str(e),
        )


def main():
    parser = argparse.ArgumentParser(description="Resume Analyzer E2E Runner")
    parser.add_argument("--folder", default=FOLDER_ID, help="Google Drive folder ID")
    parser.add_argument("--output", default="e2e_results.csv", help="Output CSV path")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS_OUTER)
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("Resume Analyzer — E2E Test Run")
    log.info("=" * 60)
    log.info(f"Folder ID : {args.folder}")
    log.info(f"Output    : {args.output}")
    log.info(f"Workers   : {args.workers}")
    log.info("")
    log.info("Manager Criteria:")
    for k, v in CRITERIA.items():
        log.info(f"  {k}: {v[:80]}...")
    log.info("=" * 60)

    log.info("Authenticating with Google Drive...")
    service = get_drive_service()

    log.info(f"Listing resumes in folder {args.folder}...")
    resume_files = list_resume_files(service, args.folder)
    log.info(f"Found {len(resume_files)} resume(s)")

    if not resume_files:
        log.error(
            "No resumes found. Check:\n"
            f"  1. Folder ID is correct: {args.folder}\n"
            f"  2. Service account has access: resume-analyzer@mad-project5372.iam.gserviceaccount.com\n"
            "  3. Folder contains PDF, DOCX, DOC, or Google Doc files"
        )
        sys.exit(1)

    # Log file breakdown by type
    from collections import Counter
    type_counts = Counter(rf.mime_type.split(".")[-1] for rf in resume_files)
    for mime, count in Counter(rf.mime_type for rf in resume_files).items():
        log.info(f"  {count}x {mime}")

    agent1 = create_agent1(CRITERIA["Q1"], CRITERIA["Q2"])
    agent2 = create_agent2(CRITERIA["Q3"], CRITERIA["Q4"])
    agent3 = create_agent3(CRITERIA["JD"])
    contact_extractor = ContactExtractor()
    image_parser = ImageParser()

    results = []
    errors = 0
    live_csv = LiveCsvWriter(args.output)

    log.info(f"\nProcessing {len(resume_files)} resumes (streaming results to {args.output})...")
    with ThreadPoolExecutor(max_workers=args.workers) as outer:
        futures = {
            outer.submit(
                process_single_resume,
                rf, agent1, agent2, agent3, contact_extractor, image_parser
            ): rf
            for rf in resume_files
        }
        for i, future in enumerate(as_completed(futures), 1):
            rf = futures[future]
            result = future.result()
            live_csv.append(result)
            results.append(result)
            if result.error:
                errors += 1
                log.warning(f"[{i:3}/{len(resume_files)}] {rf.name:<50} ERROR: {result.error[:60]}")
            else:
                log.info(
                    f"[{i:3}/{len(resume_files)}] {rf.name:<50} "
                    f"Q1={result.scores.score_q1:2} Q2={result.scores.score_q2:2} "
                    f"Q3={result.scores.score_q3:2} Q4={result.scores.score_q4:2} "
                    f"Q5={result.scores.score_q5:2} TOTAL={result.scores.total:3}"
                )

    # Re-write sorted by score at the end
    write_results_to_csv(results, args.output)

    # ── Summary ──────────────────────────────────────────────────────────────
    successful = [r for r in results if not r.error]
    scores = [r.scores.total for r in successful]
    avg = sum(scores) / len(scores) if scores else 0

    log.info("\n" + "=" * 60)
    log.info("E2E Run Complete")
    log.info(f"  Total processed : {len(results)}")
    log.info(f"  Successful      : {len(successful)}")
    log.info(f"  Errors          : {errors}")
    if scores:
        log.info(f"  Score range     : {min(scores)} – {max(scores)}")
        log.info(f"  Average score   : {avg:.1f}/100")

    # Top 5
    sorted_results = sorted(successful, key=lambda r: r.scores.total, reverse=True)
    log.info("\nTop 5 Candidates:")
    for rank, r in enumerate(sorted_results[:5], 1):
        name = r.contact.name or r.file.name
        log.info(f"  #{rank}  {name:<35} score={r.scores.total}/100")

    log.info(f"\nResults written to: {args.output}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
