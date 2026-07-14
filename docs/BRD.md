# Business Requirements Document: AP Invoice Processing Automation

**Status:** Validated against test set (see Section 8)
**Owner:** Harshit Sharma
**Last updated:** 15/07/26

## 1. Problem statement

Accounts payable teams manually review every incoming invoice against its
purchase order before approving payment. For high-volume vendors, this is
repetitive, low-judgment work: most invoices match their PO exactly and
need no human decision at all. The manual process still touches every
invoice equally, which means genuine exceptions (mismatched amounts,
missing documentation, duplicate submissions) compete for attention with
invoices that require no review whatsoever.

## 2. Objective

Automatically process routine, rule-compliant invoices end-to-end with zero
human touch, while reliably surfacing genuine exceptions to a human
reviewer with enough context to resolve them in one pass.

## 3. Scope

**In scope:**
- Single-page PDF invoices with a referenced PO number
- Matching against an existing PO/vendor master
- Auto-approval of invoices within tolerance
- Escalation of exceptions with a plain-English explanation

**Out of scope (this version):**
- Multi-page invoices with complex line-item structures
- Invoices in currencies other than the PO's currency
- Automatic creation of new vendor records
- Direct payment execution (this system recommends/posts a decision; it does not move money)

## 4. Process trigger

An invoice PDF becomes available in the intake location (in production: an
email inbox or AP portal upload; in this demo: a watched folder).

## 5. Actors

| Actor | Role |
|---|---|
| AP system (this workflow) | Extracts, matches, decides, posts or escalates |
| Finance/AP reviewer | Resolves escalated exceptions |
| PO/vendor master | System of record the workflow checks against |

## 6. Data requirements

Extracted from each invoice:

| Field | Required? | Notes |
|---|---|---|
| Vendor name | Yes | Used for vendor-on-file check |
| Invoice number | Yes | Used for duplicate detection |
| Invoice date | No | Captured but not currently used in decisioning |
| Total amount | Yes | Compared against PO amount |
| PO number | No | Absence itself is a decision input |
| Line items | No | Captured for audit trail, not currently used in decisioning |

## 7. Decision logic summary

See `decision_rules.md` for the full, versioned rule set. Summary: an
invoice auto-approves only if all of the following hold: a matching PO is
found, the vendor is on file, the amount is within tolerance of the PO
amount, and the invoice number hasn't been seen before. Any single failure
routes to human review with a specific explanation of which rule failed
and why.

## 8. Validation results (test run, [date])

Processed against a 6-invoice synthetic test set covering every rule:

| Result | Count | Rate |
|---|---|---|
| Auto-approved (touchless) | 2 | 33% |
| Flagged for review | 4 | 67% |

All 4 exceptions were correctly categorized, including one invoice that
triggered two simultaneous rule violations (missing PO **and** unknown
vendor) and one borderline case that correctly auto-approved at 0.96%
variance against a 2% threshold. Full case-by-case detail in
`decision_rules.md`.

## 9. Success metrics (production)

- **Touchless rate**: % of invoices requiring zero human review
- **Cycle time**: time from invoice receipt to posted/escalated status
- **Extraction accuracy**: % of fields correctly extracted vs. source document
- **False escalation rate**: % of flagged invoices a human found to actually be clean (signals tolerance is too tight)
- **Missed exception rate**: % of auto-approved invoices later found to have had a real problem (signals tolerance is too loose)

## 10. Assumptions & open questions

- Assumes the PO/vendor master is accurate and current; the workflow trusts it as ground truth
- 2% variance tolerance is a starting assumption, not a validated business figure -- needs sign-off from AP leadership
- Duplicate detection is based on exact invoice number match; does not currently catch near-duplicate submissions (e.g. re-typed invoice numbers)

## 11. Future enhancements

- Multi-line-item reconciliation (match individual lines, not just totals)
- Configurable tolerance by vendor or spend category
- Auto-suggest the correct PO when one is missing but inferable from vendor + amount