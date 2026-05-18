"""Streamlit dashboard for the Insurance Claims Agent."""
from __future__ import annotations

import json
import os

import requests
import streamlit as st

API_URL = os.getenv("CLAIMS_API_URL", "http://localhost:8000/process-claim")

st.set_page_config(page_title="Insurance Claims Agent", page_icon="📄", layout="wide")
st.title("📄 Autonomous Insurance Claims Processing Agent")
st.caption("Upload a FNOL document (PDF or TXT) to extract, validate and route the claim.")

uploaded = st.file_uploader("Upload claim document", type=["pdf", "txt"])

if uploaded is not None:
    if st.button("Process claim", type="primary"):
        with st.spinner("Processing..."):
            try:
                files = {"file": (uploaded.name, uploaded.getvalue())}
                r = requests.post(API_URL, files=files, timeout=120)
                r.raise_for_status()
                result = r.json()
            except Exception as exc:
                st.error(f"Request failed: {exc}")
                st.stop()

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("🧩 Extracted Fields")
            st.json(result.get("extractedFields", {}))

        with col2:
            st.subheader("🚦 Routing Decision")
            route = result.get("recommendedRoute", "—")
            st.metric("Recommended Route", route)

            missing = result.get("missingFields", [])
            if missing:
                st.warning(f"Missing fields ({len(missing)}):")
                for m in missing:
                    st.write(f"• {m}")
            else:
                st.success("All mandatory fields present ✅")

        st.subheader("🧠 Reasoning")
        st.info(result.get("reasoning", ""))

        st.subheader("📦 Raw JSON")
        st.code(json.dumps(result, indent=2), language="json")
