from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP, CHROMA_COLLECTION_NAME


def _extract_text(file_path: str) -> str:
    """Extract raw text from PDF or TXT file."""
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        return "".join(page.extract_text() or "" for page in reader.pages)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks for better retrieval."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_text(text)


def ingest_file(file_path: str) -> int:
    """
    Full pipeline: file → extract text → chunk → store in ChromaDB.
    Returns number of chunks stored.
    """
    text = _extract_text(file_path)

    if not text.strip():
        raise ValueError("No text could be extracted from the file.")

    chunks = _chunk_text(text)

    client = chromadb.Client()
    collection = client.get_or_create_collection(CHROMA_COLLECTION_NAME)

    collection.add(
        documents=chunks,
        ids=[f"{file_path}_chunk_{i}" for i in range(len(chunks))],
        metadatas=[{"source": file_path} for _ in chunks],
    )

    return len(chunks)


def clear_collection():
    """Delete all stored notes from vector DB."""
    client = chromadb.Client()
    try:
        client.delete_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        pass