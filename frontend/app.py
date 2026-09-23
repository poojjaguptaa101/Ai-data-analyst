"""
Streamlit frontend for the AI Data Analyst. Talks to the FastAPI backend
over HTTP. Run backend first (see README), then:
    streamlit run frontend/app.py
"""
import os
import requests
import streamlit as st
import plotly.io as pio

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Data Analyst", layout="wide")
st.title("📊 AI-Powered Data Analyst")

if "session_id" not in st.session_state:
    resp = requests.post(f"{BACKEND_URL}/session")
    st.session_state.session_id = resp.json()["session_id"]
    st.session_state.messages = []
    st.session_state.uploaded = False

with st.sidebar:
    st.header("Upload data")
    files = st.file_uploader("Upload one or more CSV files", type="csv", accept_multiple_files=True)
    if files and st.button("Upload"):
        payload = [("files", (f.name, f.getvalue(), "text/csv")) for f in files]
        resp = requests.post(
            f"{BACKEND_URL}/upload",
            params={"session_id": st.session_state.session_id},
            files=payload,
        )
        if resp.ok:
            st.session_state.uploaded = True
            for ds in resp.json()["datasets"]:
                st.success(f"Loaded {ds['name']}: {ds['rows']} rows, {len(ds['columns'])} columns")
        else:
            st.error(resp.json().get("detail", "Upload failed."))

    st.markdown("---")
    st.caption("Example questions:")
    for q in [
        "Which region generated the highest revenue?",
        "Show monthly sales trends.",
        "What are the top five customers?",
        "Detect anomalies in the dataset.",
    ]:
        st.caption(f"• {q}")

for msg in st.session_state.get("messages", []):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("chart"):
            st.plotly_chart(pio.from_json(msg["chart"]), use_container_width=True)

if prompt := st.chat_input("Ask a question about your data..."):
    if not st.session_state.get("uploaded"):
        st.warning("Please upload a CSV file first.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                resp = requests.post(
                    f"{BACKEND_URL}/query",
                    json={"session_id": st.session_state.session_id, "question": prompt},
                )
            if resp.ok:
                data = resp.json()
                st.write(data["answer"])
                chart_json = None
                for artifact in data.get("artifacts", []):
                    if artifact["type"] == "chart":
                        chart_json = artifact["data"]["chart_json"]
                        st.plotly_chart(pio.from_json(chart_json), use_container_width=True)
                st.session_state.messages.append(
                    {"role": "assistant", "content": data["answer"], "chart": chart_json}
                )
            else:
                st.error(resp.json().get("detail", "Query failed."))
