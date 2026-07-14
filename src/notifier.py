"""
For approved invoices, nothing happens here -- the whole point of automation
is that clean cases need zero human attention. For exceptions, this module
asks the configured LLM (Claude or Gemini) to draft a short, specific,
plain-English explanation of what's wrong, then "sends" it (console output
for this demo; swap send_alert's body for a real Slack webhook call in
production).
"""
from src.llm_client import generate_text
from src.schema import Decision, ExtractedInvoice, MatchResult

EXPLANATION_PROMPT_TEMPLATE = """An AP invoice was flagged for human review. Write a
short (2-3 sentence), specific explanation a finance analyst can act on immediately --
state the exact numbers involved, not just the category of problem.

Invoice: {invoice_number} from {vendor_name}, total ${total_amount:,.2f}
PO referenced: {po_number}
Exception reasons: {reasons}
Matched PO amount: {po_amount}
Variance: {variance_pct}

Write only the explanation, no preamble."""


def draft_explanation(extracted: ExtractedInvoice, match: MatchResult, decision: Decision) -> str:
    prompt = EXPLANATION_PROMPT_TEMPLATE.format(
        invoice_number=extracted.invoice_number,
        vendor_name=extracted.vendor_name,
        total_amount=extracted.total_amount,
        po_number=extracted.po_number or "none provided",
        reasons=", ".join(r.value for r in decision.exception_reasons),
        po_amount=f"${match.po_amount:,.2f}" if match.po_amount else "n/a",
        variance_pct=f"{match.variance_pct:.1f}%" if match.variance_pct is not None else "n/a",
    )

    return generate_text(prompt).strip()


def send_alert(explanation: str, invoice_number: str):
    """Console/log alert for this demo. To go to Slack instead, POST
    {'text': message} to config.SLACK_WEBHOOK_URL with requests.post()."""
    print(f"\n[EXCEPTION ALERT] Invoice {invoice_number}")
    print(f"  {explanation}\n")