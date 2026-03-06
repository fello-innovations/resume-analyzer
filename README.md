# Resume Analyzer

An AI-powered resume screening pipeline that pulls resumes from Google Drive, parses all common formats, and scores each candidate against custom hiring criteria using **Qwen 3.5** via OpenRouter.

---

## Features

- **Google Drive integration** — reads resumes directly from any Drive folder (including shared/Team Drives)
- **Multi-format parsing** — handles `.pdf` (text + image-based via vision LLM), `.docx`, `.doc`, and Google Docs
- **5 scoring agents** — each scores on a 0–20 scale for a 100-point total
  - Agent 1: Ideal profile match
  - Agent 2: Deal-breaker check
  - Agent 3: Prior experience signals
  - Agent 4: Required tools & skills
  - Agent 5: Job description (JD) match
- **Contact extraction** — name, email, phone, LinkedIn via regex + LLM fallback
- **Strict AI scoring** — temperature 0.7, thinking mode enabled, 5-tier rubric to avoid score inflation
- **Parallel processing** — outer pool per resume, inner pool for concurrent agents
- **CSV output** — ranked results sorted by total score

---

## Output CSV Columns

```
name, email, phone, linkedin, resume_url, score_q1, score_q2, score_q3, score_q4, score_q5, total_score, error
```

---

## Project Structure

```
resume_analzer/
├── agents/
│   ├── agent1.py          # Scores ideal profile + deal breakers (Q1, Q2)
│   ├── agent2.py          # Scores experience signals + tools (Q3, Q4)
│   ├── agent3.py          # Scores JD match (Q5)
│   ├── contact_extractor.py
│   └── scoring_agent.py   # Base class (LLM call, JSON parse, retry logic)
├── gdrive/
│   ├── auth.py            # Google Drive service account auth
│   └── fetcher.py         # List + download files from Drive folder
├── models/
│   └── schemas.py         # Dataclasses: ResumeResult, ContactInfo, Scores
├── output/
│   └── csv_writer.py      # Writes ranked CSV
├── parsers/
│   ├── pdf_parser.py      # pdfplumber + image fallback detection
│   ├── docx_parser.py     # python-docx (paragraphs + tables)
│   ├── gdoc_parser.py     # Google Docs export as plain text
│   └── image_parser.py    # Vision LLM for image-based PDFs
├── tests/
│   ├── unit/              # Unit tests per module
│   └── integration/       # Full pipeline integration tests
├── main.py                # Interactive CLI (prompts manager for criteria + JD)
├── run_e2e.py             # Non-interactive runner (criteria pre-filled)
├── config.py              # Env vars + constants
└── requirements.txt
```

---

## Prerequisites

- Python 3.10+
- A **Google Cloud service account** with Drive API enabled
- An **OpenRouter API key** (for Qwen 3.5 and vision model)
- Poppler installed (for PDF-to-image conversion)

### Install Poppler

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/resume-analyzer.git
cd resume-analyzer
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Google Drive credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → enable **Google Drive API**
3. Create a **Service Account** → download the JSON key
4. Save it as `credentials.json` in the project root
5. Share your Drive folder with the service account's email address

### 5. Configure environment variables

Create a `.env.local` file in the project root:

```env
OPENROUTER_API_KEY=sk-or-...your-key...
TOGETHER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=qwen/qwen3.5-plus-02-15
LLM_VISION_MODEL=qwen/qwen-vl-plus
MAX_WORKERS_OUTER=4
IMAGE_TEXT_THRESHOLD=100
IMAGE_BATCH_SIZE=5
OUTPUT_CSV=results.csv
```

> **Note:** `TOGETHER_API_KEY` is read from `OPENROUTER_API_KEY` internally — just set `OPENROUTER_API_KEY`.

### 6. Share your Drive folder with the service account

In Google Drive, right-click your resumes folder → **Share** → paste the service account email (found in `credentials.json` under `client_email`).

---

## Usage

### Interactive mode (recommended for production)

```bash
python main.py
```

You'll be prompted to enter:
1. Google Drive folder ID
2. Your ideal candidate profile (Q1)
3. Deal breakers (Q2)
4. Prior experience signals to look for (Q3)
5. Required tools/skills (Q4)
6. Full Job Description — paste or press Enter to skip (Q5)

Results are saved to `results.csv`.

### Non-interactive / scripted mode

Edit the `CRITERIA` dict and folder ID at the top of `run_e2e.py`, then:

```bash
python run_e2e.py
# or with custom folder/output:
python run_e2e.py --folder <folder_id> --output my_results.csv
```

---

## How to get your Google Drive Folder ID

From the folder URL:
```
https://drive.google.com/drive/folders/1TXQSGyUFcK8xpU_7lPkG8qXlvIMHp_bl
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                        This is your folder ID
```

---

## Running Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

All 25 tests should pass.

---

## Scoring System

Each resume is scored across 5 dimensions (0–20 each, 100 total):

| Dimension | Agent | What it measures |
|-----------|-------|-----------------|
| Q1 | Agent 1 | How well the candidate matches the ideal profile description |
| Q2 | Agent 1 | Whether the candidate has any deal breakers |
| Q3 | Agent 2 | Prior experience signals (industry, company stage, etc.) |
| Q4 | Agent 2 | Required tools, technologies, or skills |
| Q5 | Agent 3 | Match against the full Job Description |

**Scoring rubric (applied strictly):**
- 18–20: Truly exceptional — rare
- 14–17: Strong match, minor gaps
- 9–13: Moderate match, notable gaps
- 4–8: Weak match, significant gaps
- 0–3: Poor or no match

---

## Architecture Notes

- **Thread safety**: Each worker thread creates its own Google Drive service client (httplib2 is not thread-safe)
- **Thinking mode**: Qwen 3's `<think>...</think>` blocks are stripped before JSON parsing
- **Vision fallback**: PDFs with fewer than 100 characters of extracted text are treated as image-based and sent to the vision model in batches
- **Retry logic**: LLM calls retry up to 3 times with 1-second backoff

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `404 File not found` for Drive folder | Make sure the folder is shared with the service account email |
| `SSL record layer failure` | Don't share a single Drive service across threads — each thread needs its own |
| Scores too generous (everyone 90+) | Ensure thinking mode is on and temperature ≥ 0.7 in `scoring_agent.py` |
| Image PDFs not parsed | Install poppler: `brew install poppler` |
| `credentials.json` not found | Download service account key from Google Cloud Console |

---

## License

MIT
