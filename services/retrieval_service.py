import chromadb
from config.settings import CHROMA_COLLECTION_NAME, TOP_K_RESULTS


def retrieve_relevant_chunks(query: str) -> list[str]:
    """
    Search ChromaDB for chunks most relevant to the user's question.
    Returns list of matching text chunks.
    """
    client = chromadb.Client()

    try:
        collection = client.get_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        raise RuntimeError("No notes found. Please upload a file first.")

    results = collection.query(
        query_texts=[query],
        n_results=TOP_K_RESULTS,
    )

    return results["documents"][0]