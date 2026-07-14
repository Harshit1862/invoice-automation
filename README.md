# AP invoice automation — digital employee demo

A minimal "digital employee" that owns AP invoice processing end to end:
reads an invoice PDF, matches it against a PO database, auto-posts clean
invoices, and escalates genuine exceptions with a plain-English explanation
instead of a raw error code.

## Why this exists

Built as a portfolio project demonstrating the business-analyst-to-workflow
translation skillset: capturing process requirements, encoding them as
explicit decision rules, implementing with an LLM in the loop, and
measuring the result against KPIs (touchless rate, cycle time, accuracy).

## Results

Processed a 6-invoice test set: 33% fully touchless (auto-approved with zero
human review), remaining 4 correctly escalated with a specific, actionable
explanation for each — including one invoice that correctly triggered two
simultaneous exception rules.

![KPI dashboard](docs/dashboard-screenshot.png)

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your GEMINI_API_KEY (see .env.example)
```

## Run

```bash
python scripts/generate_synthetic_invoices.py   # creates the 6 test invoices
pytest tests/                                    # 12 offline tests, no API calls
python scripts/run_batch.py                      # processes data/invoices/
streamlit run dashboard/app.py                   # view KPI dashboard
```

## Project status

- [x] Project scaffold
- [x] Data schema (`src/schema.py`)
- [x] Mock PO database (`data/po_database.csv`)
- [x] Extraction (`src/extraction.py`, provider-agnostic via `src/llm_client.py`)
- [x] Matching logic (`src/matching.py`)
- [x] Decision engine (`src/decision.py`)
- [x] Exception notifier (`src/notifier.py`)
- [x] Pipeline orchestration (`src/pipeline.py`)
- [x] Dashboard (`dashboard/app.py`)
- [x] Test suite (`tests/`, 12 tests, fully offline)
- [x] BRD (`docs/BRD.md`) and decision rules (`docs/decision_rules.md`)

## Architecture notes

- **Provider-agnostic LLM calls**: `src/llm_client.py` abstracts extraction
  and text generation behind two functions, so switching between Claude and
  Gemini is a one-line `.env` change, not a code change. Defaults to Gemini
  (free tier); set `LLM_PROVIDER=anthropic` once you have API credits.
- **Every processing attempt is logged**, not just the latest state per
  invoice number — a resubmitted invoice IS the duplicate-detection signal,
  so it must stay in the history rather than overwrite the prior attempt.