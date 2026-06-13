import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".xlsx"}

st.set_page_config(page_title="RAG Chatbot", page_icon="💬", layout="centered")
st.title("RAG Chatbot")

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []


def check_api_status() -> bool:
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        return response.ok
    except requests.RequestException:
        return False


def send_chat(message: str) -> dict | None:
    payload = {"message": message, "session_id": st.session_state.session_id}
    response = requests.post(f"{API_URL}/chat", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def upload_document(file) -> dict | None:
    files = {"file": (file.name, file.getvalue())}
    response = requests.post(f"{API_URL}/ingest", files=files, timeout=120)
    response.raise_for_status()
    return response.json()


with st.sidebar:
    st.header("Settings")

    if check_api_status():
        st.success("API connected")
    else:
        st.error(f"Cannot reach API at {API_URL}")

    if st.button("New Chat", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("Upload Document")
    uploaded = st.file_uploader(
        "PDF, TXT, XLSX, or MD",
        type=["pdf", "txt", "md", "xlsx"],
        label_visibility="collapsed",
    )
    if uploaded is not None:
        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            st.error(f"Unsupported file type: {suffix}")
        elif st.button("Ingest file", use_container_width=True):
            with st.spinner("Uploading and indexing..."):
                try:
                    result = upload_document(uploaded)
                    st.success(
                        f"Stored {result['chunks_stored']} chunks from {result['filename']}"
                    )
                except requests.ConnectionError:
                    st.error("Cannot connect to the API. Is FastAPI running?")
                except requests.HTTPError as exc:
                    detail = exc.response.text if exc.response is not None else str(exc)
                    st.error(f"Upload failed: {detail}")

    st.divider()
    st.caption("Session ID")
    st.code(st.session_state.session_id or "New session on first message")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("Sources"):
                for source in msg["sources"]:
                    st.text(source)

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = send_chat(prompt)
                st.session_state.session_id = result["session_id"]
                answer = result["answer"]
                sources = result.get("sources", [])
                st.markdown(answer)
                if sources:
                    with st.expander("Sources"):
                        for source in sources:
                            st.text(source)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )
            except requests.ConnectionError:
                st.error("Cannot connect to the API. Is FastAPI running?")
            except requests.HTTPError as exc:
                detail = exc.response.text if exc.response is not None else str(exc)
                st.error(f"Request failed: {detail}")
