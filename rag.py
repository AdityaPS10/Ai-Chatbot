import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader, TextLoader,UnstructuredExcelLoader
 
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = Chroma(
    collection_name="documents",
    embedding_function=embeddings,
    persist_directory="./chroma_store",
)

llm = Ollama(model=os.getenv("OLLAMA_MODEL", "phi3"))

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def ingest_file(file_path: str) -> int:
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".xlsx"):
        loader = UnstructuredExcelLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")

    docs = loader.load()
    chunks = splitter.split_documents(docs)
    vector_store.add_documents(chunks)
    return len(chunks)


def ask(question: str, history: list[dict]) -> dict:
    """
    Retrieve relevant chunks from ChromaDB, build a prompt,
    and get an answer from the LLM.
    """
    results = vector_store.similarity_search(question, k=4)
    context = "\n\n".join(doc.page_content for doc in results)
    sources = list({doc.metadata.get("source", "unknown") for doc in results})

    # Build conversation history string
    history_text = ""
    for msg in history[-6:]:   # last 3 exchanges
        prefix = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{prefix}: {msg['content']}\n"

    # Simple prompt
    prompt = f"""You are a helpful assistant. Use the context below to answer.
If the context is not relevant, answer from your own knowledge.

Context:
{context}

Conversation so far:
{history_text}
User: {question}
Assistant:"""

    answer = llm.invoke(prompt)
    return {"answer": answer, "sources": sources}
