"""
Streamlit KPI dashboard reading from the mock ERP's invoice_log table.

Run: streamlit run dashboard/app.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st

from src import database

st.set_page_config(page_title="AP Invoice Automation - KPI Dashboard", layout="wide")
st.title("AP invoice automation -- KPI dashboard")

rows = database.fetch_all_logged_invoices()

if not rows:
    st.info("No invoices processed yet. Run `python scripts/run_batch.py` first.")
    st.stop()

df = pd.DataFrame(rows)
total = len(df)
approved = df["approved"].sum()
touchless_rate = approved / total * 100
avg_seconds = df["processing_seconds"].mean()

col1, col2, col3 = st.columns(3)
col1.metric("Touchless rate", f"{touchless_rate:.0f}%")
col2.metric("Invoices processed", total)
col3.metric("Avg. processing time", f"{avg_seconds:.1f}s")

st.subheader("Exception breakdown")
exceptions_df = df[df["approved"] == 0]
if not exceptions_df.empty:
    reason_counts = (
        exceptions_df["exception_reasons"]
        .str.split(",")
        .explode()
        .value_counts()
    )
    st.bar_chart(reason_counts)
else:
    st.write("No exceptions logged.")

st.subheader("Invoice log")
st.dataframe(df, use_container_width=True)