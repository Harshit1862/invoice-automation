"""
Pure unit tests for the decision engine -- no database, no API calls needed.
This is deliberately the fastest, most reliable layer of the test suite: if
these fail, the actual business rules are wrong, which is the most important
thing to catch before anything else.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.decision import decide
from src.schema import ExceptionReason, ExtractedInvoice, MatchResult


def make_invoice(**overrides):
    defaults = dict(
        vendor_name="Acme Office Supplies",
        invoice_number="TEST-001",
        total_amount=1000.0,
        po_number="PO-1001",
    )
    defaults.update(overrides)
    return ExtractedInvoice(**defaults)


def test_clean_match_is_approved():
    invoice = make_invoice()
    match = MatchResult(po_found=True, po_amount=1000.0, variance_pct=0.0,
                         vendor_on_file=True, is_duplicate=False)
    result = decide(invoice, match)
    assert result.approved is True
    assert result.exception_reasons == []


def test_amount_mismatch_over_threshold_flagged():
    invoice = make_invoice(total_amount=1200.0)
    match = MatchResult(po_found=True, po_amount=1000.0, variance_pct=20.0,
                         vendor_on_file=True, is_duplicate=False)
    result = decide(invoice, match)
    assert result.approved is False
    assert ExceptionReason.AMOUNT_MISMATCH in result.exception_reasons


def test_amount_within_tolerance_is_approved():
    invoice = make_invoice(total_amount=1015.0)
    match = MatchResult(po_found=True, po_amount=1000.0, variance_pct=1.5,
                         vendor_on_file=True, is_duplicate=False)
    result = decide(invoice, match)
    assert result.approved is True


def test_missing_po_flagged():
    invoice = make_invoice(po_number=None)
    match = MatchResult(po_found=False, po_amount=None, variance_pct=None,
                         vendor_on_file=True, is_duplicate=False)
    result = decide(invoice, match)
    assert result.approved is False
    assert ExceptionReason.NO_PO_FOUND in result.exception_reasons


def test_unknown_vendor_flagged():
    invoice = make_invoice()
    match = MatchResult(po_found=True, po_amount=1000.0, variance_pct=0.0,
                         vendor_on_file=False, is_duplicate=False)
    result = decide(invoice, match)
    assert result.approved is False
    assert ExceptionReason.VENDOR_NOT_ON_FILE in result.exception_reasons


def test_duplicate_invoice_flagged():
    invoice = make_invoice()
    match = MatchResult(po_found=True, po_amount=1000.0, variance_pct=0.0,
                         vendor_on_file=True, is_duplicate=True)
    result = decide(invoice, match)
    assert result.approved is False
    assert ExceptionReason.DUPLICATE_INVOICE in result.exception_reasons


def test_multiple_exceptions_all_captured():
    invoice = make_invoice(po_number=None)
    match = MatchResult(po_found=False, po_amount=None, variance_pct=None,
                         vendor_on_file=False, is_duplicate=True)
    result = decide(invoice, match)
    assert result.approved is False
    assert len(result.exception_reasons) == 3