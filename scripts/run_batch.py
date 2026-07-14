"""
CLI entry point: processes every invoice in data/invoices/ and prints a summary.

Usage: python scripts/run_batch.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import config, pipeline


def main():
    results = pipeline.process_batch(config.INVOICES_DIR)

    total = len(results)
    approved = sum(1 for r in results if r.approved)
    touchless_rate = (approved / total * 100) if total else 0

    print("\n" + "=" * 50)
    print("BATCH SUMMARY")
    print("=" * 50)
    print(f"Total invoices processed: {total}")
    print(f"Auto-approved (touchless): {approved} ({touchless_rate:.0f}%)")
    print(f"Flagged for review: {total - approved}")
    for r in results:
        if not r.approved:
            print(f"  - {r.invoice_number}: {', '.join(x.value for x in r.exception_reasons)}")


if __name__ == "__main__":
    main()