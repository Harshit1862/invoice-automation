"""
Orchestrates the full flow for one invoice: extract -> match -> decide ->
post or alert -> log. This is the file that turns the individual modules
into an actual "digital employee" that owns the process end to end.
"""
import glob
import os
import time

from src import database, decision as decision_module, extraction, matching, notifier
from src.schema import Decision


def process_invoice(pdf_path: str) -> Decision:
    start = time.time()

    extracted = extraction.extract_invoice(pdf_path)
    match = matching.match_invoice(extracted)
    decision = decision_module.decide(extracted, match)

    if decision.approved:
        # Touchless path -- no human involved
        print(f"[APPROVED] {decision.invoice_number} -- posted to ERP automatically")
    else:
        explanation = notifier.draft_explanation(extracted, match, decision)
        decision.explanation = explanation
        notifier.send_alert(explanation, decision.invoice_number)

    elapsed = time.time() - start
    database.log_invoice(extracted, decision, elapsed)

    return decision


def process_batch(invoices_dir: str) -> list[Decision]:
    database.init_db()
    results = []
    for pdf_path in sorted(glob.glob(os.path.join(invoices_dir, "*.pdf"))):
        print(f"\nProcessing {os.path.basename(pdf_path)} ...")
        try:
            results.append(process_invoice(pdf_path))
        except Exception as e:
            print(f"[ERROR] Failed to process {pdf_path}: {e}")
        time.sleep(4)
    return results