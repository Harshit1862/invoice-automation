"""
Compares an extracted invoice against the PO database and returns a MatchResult.
This is intentionally simple, deterministic logic -- no LLM involved. High-volume,
rule-based checks like this are exactly where automation has the fastest payback,
so keeping it transparent and testable matters more than being clever.
"""
from src import config, database
from src.schema import ExtractedInvoice, MatchResult


def match_invoice(extracted: ExtractedInvoice, db_path: str = config.ERP_DB_PATH) -> MatchResult:
    po = database.get_po(extracted.po_number, db_path=db_path) if extracted.po_number else None
    po_found = po is not None

    variance_pct = None
    if po_found:
        variance_pct = abs(extracted.total_amount - po["po_amount"]) / po["po_amount"] * 100

    vendor_on_file = database.vendor_exists(extracted.vendor_name, db_path=db_path)
    is_duplicate = database.is_duplicate_invoice(extracted.invoice_number, db_path=db_path)

    return MatchResult(
        po_found=po_found,
        po_amount=po["po_amount"] if po_found else None,
        variance_pct=variance_pct,
        vendor_on_file=vendor_on_file,
        is_duplicate=is_duplicate,
    )