"""
Sends an invoice PDF to an LLM (Claude or Gemini, via llm_client) and
returns a validated ExtractedInvoice.

Why an LLM instead of regex/OCR templates: invoices from different vendors
have wildly inconsistent layouts. A template-based extractor breaks the
moment a new vendor's format shows up; an LLM reads the document the way
a person would and returns the same structured shape regardless of layout.

The Pydantic validation step is what makes this safe to put in a pipeline --
if the model's output doesn't match the schema, we fail loudly here instead
of letting a malformed record flow into the "ERP".
"""
import json

from src.llm_client import extract_json_from_pdf as llm_extract_json_from_pdf
from src.schema import ExtractedInvoice

EXTRACTION_PROMPT = """You are extracting structured data from an invoice PDF for an
accounts payable workflow. Read the document carefully and return ONLY a JSON object
(no markdown fences, no preamble) with exactly these fields:

{
  "vendor_name": string,
  "invoice_number": string,
  "invoice_date": string in YYYY-MM-DD format, or null if not present,
  "total_amount": number,
  "po_number": string, or null if no PO number appears on the invoice,
  "line_items": [
    {"description": string, "quantity": number, "unit_price": number, "line_total": number}
  ],
  "extraction_confidence_notes": string or null -- note anything ambiguous,
    illegible, or that you had to infer rather than read directly
}

Return the total_amount exactly as printed on the invoice, even if it looks
inconsistent with the line items -- do not recalculate it. If a field is
genuinely absent from the document, use null rather than guessing."""


def extract_invoice(pdf_path: str) -> ExtractedInvoice:
    raw_text = llm_extract_json_from_pdf(pdf_path, EXTRACTION_PROMPT).strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Model did not return valid JSON for {pdf_path}: {e}\nRaw output: {raw_text}"
        )

    return ExtractedInvoice.model_validate(data)


if __name__ == "__main__":
    import sys

    result = extract_invoice(sys.argv[1] if len(sys.argv) > 1 else "data/invoices/inv_clean_match.pdf")
    print(result.model_dump_json(indent=2))