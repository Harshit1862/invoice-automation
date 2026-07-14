# Decision Rules: AP Invoice Processing

**Version:** 1.0
**Effective:** 15/07/26
**Owner:** Harshit Sharma

This document is the single source of truth for what counts as an
exception. It should always match `src/decision.py` exactly -- if they
diverge, the code is wrong, not this document.

## Approval rule

An invoice is **auto-approved** if and only if none of the four exception
conditions below are triggered. Otherwise, it is escalated to a human
reviewer with a Claude/Gemini-drafted explanation of which rule(s) failed.

## Exception conditions

### 1. No PO found (`no_po_found`)
**Trigger:** The invoice's PO number is missing, or doesn't match any PO
in the master database.
**Rationale:** Without a PO, there's no basis to verify the charge is
authorized or pre-approved.

### 2. Amount mismatch (`amount_mismatch`)
**Trigger:** `abs(invoice_total - po_amount) / po_amount > 2%`
**Rationale:** Small variances (rounding, minor fees) are normal and not
worth a human's time. Variances above 2% may indicate billing errors,
scope changes, or unauthorized charges.
**Threshold owner:** `AMOUNT_VARIANCE_TOLERANCE_PCT` in `.env` / `config.py`

### 3. Vendor not on file (`vendor_not_on_file`)
**Trigger:** The invoice's vendor name doesn't match any vendor in the PO
master (case-insensitive).
**Rationale:** Payments to unrecognized vendors carry fraud and
compliance risk and should always get human eyes.

### 4. Duplicate invoice (`duplicate_invoice`)
**Trigger:** The invoice number has already been logged by a prior run.
**Rationale:** Prevents double-payment, whether from vendor resubmission
error or intentional double-billing.

## Multiple simultaneous exceptions

An invoice can trigger more than one rule at once (e.g. no PO **and**
unknown vendor). All applicable reasons are captured and surfaced together
-- the reviewer sees the full picture in one alert, not one problem at a
time across multiple notifications.

## Validated test cases

| Invoice | Reasons triggered | Correct? |
|---|---|---|
| `inv_clean_match` (PO-1001, exact match) | none -- approved | ✅ |
| `inv_within_tolerance` (0.96% variance) | none -- approved | ✅ |
| `inv_amount_mismatch` (12% variance) | `amount_mismatch` | ✅ |
| `inv_duplicate` (resubmitted invoice number) | `duplicate_invoice` | ✅ |
| `inv_missing_po` (no PO, known vendor) | `no_po_found` only | ✅ |
| `inv_unknown_vendor` (bad PO + unknown vendor) | `no_po_found`, `vendor_not_on_file` | ✅ |

Note the `inv_missing_po` case: the vendor (Crestview Consulting) *is* on
file, so only `no_po_found` fired -- confirming the rules are independent
and precise rather than cascading into a generic "something's wrong" flag.

## Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | [date] | Initial rule set: PO match, amount tolerance, vendor check, duplicate check |