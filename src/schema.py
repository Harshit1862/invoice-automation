"""
Pydantic models define the data contract at every stage of the pipeline.
If Claude's extraction ever returns something malformed, validation fails
loudly here instead of silently corrupting a downstream record -- this is
the guardrail that makes an LLM-in-the-loop workflow trustworthy.
"""
from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    line_total: float


class ExtractedInvoice(BaseModel):
    """What Claude extracts directly from the invoice PDF."""
    vendor_name: str
    invoice_number: str
    invoice_date: Optional[date] = None
    total_amount: float
    po_number: Optional[str] = Field(
        default=None, description="Null if no PO number is present on the invoice"
    )
    line_items: list[LineItem] = []
    extraction_confidence_notes: Optional[str] = Field(
        default=None,
        description="Anything Claude was unsure about while reading the document",
    )


class ExceptionReason(str, Enum):
    NO_PO_FOUND = "no_po_found"
    AMOUNT_MISMATCH = "amount_mismatch"
    VENDOR_NOT_ON_FILE = "vendor_not_on_file"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MISSING_REQUIRED_FIELD = "missing_required_field"


class MatchResult(BaseModel):
    """Output of comparing an extracted invoice against the PO database."""
    po_found: bool
    po_amount: Optional[float] = None
    variance_pct: Optional[float] = None
    vendor_on_file: bool
    is_duplicate: bool


class Decision(BaseModel):
    """Final routing decision for one invoice."""
    invoice_number: str
    approved: bool
    exception_reasons: list[ExceptionReason] = []
    explanation: Optional[str] = Field(
        default=None, description="Human-readable reason, drafted by Claude, when flagged"
    )