import shutil
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import init_db, get_db, Message
from rag import ingest_file, ask

app = FastAPI(title="Simple RAG Chatbot")
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
def startup():
    init_db()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[str]


@app.get("/")
def root():
    return {"message": "Chatbot is running. POST /chat to start, POST /ingest to upload docs."}


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, db: Session = Depends(get_db)):
    session_id = body.session_id or str(uuid.uuid4())

    history = [
        {"role": m.role, "content": m.content}
        for m in db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at)
            .all()
    ]

    result = ask(question=body.message, history=history)


    db.add(Message(session_id=session_id, role="user",      content=body.message))
    db.add(Message(session_id=session_id, role="assistant", content=result["answer"]))
    db.commit()

    return ChatResponse(
        session_id=session_id,
        answer=result["answer"],
        sources=result["sources"],
    )


@app.post("/ingest")
def ingest(file: UploadFile = File(...)):
    allowed = {".pdf", ".txt", ".md", ".xlsx"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"File type '{suffix}' not supported. Use: {allowed}")

    dest = UPLOAD_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    chunks = ingest_file(str(dest))
    return {"filename": file.filename, "chunks_stored": chunks}


@app.get("/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at)
        .all()
    )
    return [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]
