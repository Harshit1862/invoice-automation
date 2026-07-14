"""
Tests matching logic against a temporary, isolated SQLite database -- never
touches the real project database, and needs no API key or network access.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from src import database
from src.matching import match_invoice
from src.schema import ExtractedInvoice


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database.init_db(db_path=path, po_csv_path="data/po_database.csv")
    yield path
    os.remove(path)


def test_clean_match_found(temp_db):
    invoice = ExtractedInvoice(
        vendor_name="Acme Office Supplies",
        invoice_number="TEST-100",
        total_amount=12000.0,
        po_number="PO-1001",
    )
    result = match_invoice(invoice, db_path=temp_db)
    assert result.po_found is True
    assert result.vendor_on_file is True
    assert result.variance_pct == 0.0
    assert result.is_duplicate is False


def test_missing_po_number(temp_db):
    invoice = ExtractedInvoice(
        vendor_name="Crestview Consulting",
        invoice_number="TEST-101",
        total_amount=25000.0,
        po_number=None,
    )
    result = match_invoice(invoice, db_path=temp_db)
    assert result.po_found is False


def test_unknown_vendor(temp_db):
    invoice = ExtractedInvoice(
        vendor_name="Totally Fake Vendor Co",
        invoice_number="TEST-102",
        total_amount=500.0,
        po_number="PO-1001",
    )
    result = match_invoice(invoice, db_path=temp_db)
    assert result.vendor_on_file is False


def test_amount_variance_calculated(temp_db):
    invoice = ExtractedInvoice(
        vendor_name="Beacon Logistics Inc",
        invoice_number="TEST-103",
        total_amount=9464.56,
        po_number="PO-1002",  # po_amount = 8450.50
    )
    result = match_invoice(invoice, db_path=temp_db)
    assert result.po_found is True
    assert round(result.variance_pct, 1) == 12.0


def test_duplicate_detected_after_logging(temp_db):
    invoice = ExtractedInvoice(
        vendor_name="Acme Office Supplies",
        invoice_number="TEST-104",
        total_amount=12000.0,
        po_number="PO-1001",
    )
    result_first = match_invoice(invoice, db_path=temp_db)
    assert result_first.is_duplicate is False

    from src.decision import decide
    decision = decide(invoice, result_first)
    database.log_invoice(invoice, decision, 0.5, db_path=temp_db)

    result_second = match_invoice(invoice, db_path=temp_db)
    assert result_second.is_duplicate is True