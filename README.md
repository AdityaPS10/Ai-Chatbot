# Simple RAG Chatbot

FastAPI backend + Streamlit UI. ChromaDB + Ollama + PostgreSQL.

## Setup

```bash
# 1. Activate the project venv
source simple-chatbot/bin/activate

# 2. Install dependencies (use python -m pip to target this venv)
python -m pip install -r requirements.txt

# 3. Start PostgreSQL
docker run -d --name pg \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=chatbot_db \
  -p 5432:5432 \
  postgres:16

# 4. Start Ollama + pull the model
ollama pull phi3
ollama serve   # skip if Ollama is already running as a service

# 5. Configure environment (optional — defaults work for local dev)
# DATABASE_URL=postgresql://postgres:password@127.0.0.1:5432/chatbot_db
# OLLAMA_MODEL=phi3
# API_URL=http://localhost:8000
```

## Run

Use two terminals:

**Terminal 1 — FastAPI backend:**

```bash
source simple-chatbot/bin/activate
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 — Streamlit UI:**

```bash
source simple-chatbot/bin/activate
python -m streamlit run streamlit_app.py
```

- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Chat UI: [http://localhost:8501](http://localhost:8501)

## Usage

### Streamlit UI

1. Open [http://localhost:8501](http://localhost:8501)
2. Upload a document (PDF, TXT,XLSX or MD) from the sidebar
3. Ask questions in the chat input
4. View source file paths in the **Sources** expander under assistant replies
5. Click **New Chat** to start a fresh conversation

### API (curl)

**Upload a document:**

```bash
curl -X POST http://localhost:8000/ingest -F "file=@notes.pdf"
```

**Chat:**

```bash
# New conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is in my document?"}'

# Continue (use session_id from above response)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me more", "session_id": "<id>"}'
```

**View history:**

```bash
curl http://localhost:8000/history/<session_id>
```

## Files

```
simple-chatbot/
├── main.py            # FastAPI app + all endpoints
├── streamlit_app.py   # Streamlit chat UI
├── rag.py             # ChromaDB + embeddings + Ollama
├── database.py        # PostgreSQL + SQLAlchemy
├── requirements.txt
└── .env
```

## Notes

- `chroma_store/` is created automatically on first use
- The HuggingFace embedding model (`all-MiniLM-L6-v2`) downloads on first ingest (~90 MB)
- Chat works without uploaded documents (the LLM answers from general knowledge)
- Refreshing the Streamlit page resets the UI session; PostgreSQL history is preserved server-side
- If `streamlit` fails with a module error, use `python -m streamlit run streamlit_app.py` instead of bare `streamlit` (Anaconda may shadow the venv)

