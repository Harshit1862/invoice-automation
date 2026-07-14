"""
Mock ERP / PO system of record backed by SQLite.

Two tables:
- purchase_orders: seeded once from data/po_database.csv, acts as the PO master
- invoice_log: every invoice the pipeline has ever processed, with its outcome --
  this is what the KPI dashboard reads from, and what makes duplicate detection possible

Keeping this behind small functions (not raw SQL scattered across the codebase)
means someone reviewing the project can see the exact contract each pipeline
stage relies on.
"""
import csv
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from src import config


def init_db(db_path: str = config.ERP_DB_PATH, po_csv_path: str = config.PO_DATABASE_CSV):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            po_number TEXT PRIMARY KEY,
            vendor_name TEXT NOT NULL,
            po_amount REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoice_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            vendor_name TEXT,
            total_amount REAL,
            po_number TEXT,
            approved INTEGER NOT NULL,
            exception_reasons TEXT,
            processed_at TEXT NOT NULL,
            processing_seconds REAL
        )
    """)

    # Seed PO table only if empty, so re-running doesn't duplicate rows
    cur.execute("SELECT COUNT(*) FROM purchase_orders")
    if cur.fetchone()[0] == 0:
        with open(po_csv_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = [(r["po_number"], r["vendor_name"], float(r["po_amount"]), r["status"]) for r in reader]
        cur.executemany(
            "INSERT INTO purchase_orders (po_number, vendor_name, po_amount, status) VALUES (?, ?, ?, ?)",
            rows,
        )

    conn.commit()
    conn.close()


def get_po(po_number: str, db_path: str = config.ERP_DB_PATH) -> Optional[dict]:
    if not po_number:
        return None
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT po_number, vendor_name, po_amount, status FROM purchase_orders WHERE po_number = ?",
        (po_number,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"po_number": row[0], "vendor_name": row[1], "po_amount": row[2], "status": row[3]}


def vendor_exists(vendor_name: str, db_path: str = config.ERP_DB_PATH) -> bool:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM purchase_orders WHERE LOWER(vendor_name) = LOWER(?)",
        (vendor_name,),
    )
    count = cur.fetchone()[0]
    conn.close()
    return count > 0


def is_duplicate_invoice(invoice_number: str, db_path: str = config.ERP_DB_PATH) -> bool:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM invoice_log WHERE invoice_number = ?", (invoice_number,))
    count = cur.fetchone()[0]
    conn.close()
    return count > 0


def log_invoice(extracted, decision, processing_seconds: float, db_path: str = config.ERP_DB_PATH):
    """Records the outcome of processing one invoice. Called for every invoice,
    approved or not -- every attempt gets its own row (not upserted by invoice
    number), because a resubmitted invoice number IS the duplicate-detection
    signal and must remain in the history, not overwrite the prior attempt."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO invoice_log
           (invoice_number, vendor_name, total_amount, po_number, approved,
            exception_reasons, processed_at, processing_seconds)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            extracted.invoice_number,
            extracted.vendor_name,
            extracted.total_amount,
            extracted.po_number,
            int(decision.approved),
            ",".join(r.value for r in decision.exception_reasons),
            datetime.now(timezone.utc).isoformat(),
            processing_seconds,
        ),
    )
    conn.commit()
    conn.close()


def fetch_all_logged_invoices(db_path: str = config.ERP_DB_PATH) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM invoice_log ORDER BY processed_at")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows