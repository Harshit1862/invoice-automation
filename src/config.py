"""
Central place for settings, API keys, and business rule thresholds.
Keeping thresholds here (not buried in matching.py) means anyone reviewing
the project can see the actual business rules in one glance.
"""
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# Which provider to use: "anthropic" or "gemini".
# Anthropic requires paid credits with no ongoing free tier. Gemini's free
# tier (via Google AI Studio) needs no credit card, which is why this
# defaults to gemini -- switch back to "anthropic" once you have credits.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

# --- Business rule thresholds ---
# If the invoice total differs from the matched PO by more than this
# percentage, the invoice is routed to human review instead of auto-posted.
AMOUNT_VARIANCE_TOLERANCE_PCT = float(
    os.getenv("AMOUNT_VARIANCE_TOLERANCE_PCT", "2.0")
)

# Paths
DATA_DIR = "data"
INVOICES_DIR = f"{DATA_DIR}/invoices"
PO_DATABASE_CSV = f"{DATA_DIR}/po_database.csv"
OUTPUTS_DIR = f"{DATA_DIR}/outputs"
ERP_DB_PATH = f"{OUTPUTS_DIR}/mock_erp.db"

# Models used for extraction and exception explanations
CLAUDE_MODEL = "claude-sonnet-4-6"
GEMINI_MODEL = "gemini-3.1-flash-lite"