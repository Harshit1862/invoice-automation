"""
Encodes the business rules for auto-approval vs. escalation. This file is the
literal answer to "what counts as an exception" -- it should read like a
policy document, not clever code, because that transparency is the point.
"""
from src import config
from src.schema import Decision, ExceptionReason, ExtractedInvoice, MatchResult


def decide(extracted: ExtractedInvoice, match: MatchResult) -> Decision:
    reasons: list[ExceptionReason] = []

    if not match.po_found:
        reasons.append(ExceptionReason.NO_PO_FOUND)

    if match.po_found and match.variance_pct is not None:
        if match.variance_pct > config.AMOUNT_VARIANCE_TOLERANCE_PCT:
            reasons.append(ExceptionReason.AMOUNT_MISMATCH)

    if not match.vendor_on_file:
        reasons.append(ExceptionReason.VENDOR_NOT_ON_FILE)

    if match.is_duplicate:
        reasons.append(ExceptionReason.DUPLICATE_INVOICE)

    return Decision(
        invoice_number=extracted.invoice_number,
        approved=len(reasons) == 0,
        exception_reasons=reasons,
        explanation=None,  # filled in by notifier.py only when there's an exception
    )