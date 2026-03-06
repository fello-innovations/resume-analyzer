import os
from dotenv import load_dotenv

# Load base .env first, then let .env.local override
load_dotenv()
load_dotenv(".env.local", override=True)

# Google Drive
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# OpenRouter / LLM
TOGETHER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
TOGETHER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen3.5-plus-02-15")
LLM_VISION_MODEL = os.getenv("LLM_VISION_MODEL", "qwen/qwen3.5-plus-02-15")

# Processing
MAX_WORKERS_OUTER = int(os.getenv("MAX_WORKERS_OUTER", "4"))
IMAGE_TEXT_THRESHOLD = int(os.getenv("IMAGE_TEXT_THRESHOLD", "50"))  # chars/page
IMAGE_BATCH_SIZE = int(os.getenv("IMAGE_BATCH_SIZE", "4"))

# Output
OUTPUT_CSV = os.getenv("OUTPUT_CSV", "results.csv")
