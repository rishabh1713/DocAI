import os
from dotenv import load_dotenv

load_dotenv()

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq model
LLM_MODEL = "llama-3.1-8b-instant"
LLM_TEMPERATURE = 0.2

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Retrieval
TOP_K_RESULTS = 3

# Vector DB
CHROMA_COLLECTION_NAME = "study_notes"

# File upload — includes image types now
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = [
    ".pdf", ".txt",
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"
]
