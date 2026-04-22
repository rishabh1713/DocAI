import os
from dotenv import load_dotenv

load_dotenv()

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ✅ Updated model — llama3-8b-8192 is decommissioned
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.2

# Vision model for OCR
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Retrieval
TOP_K_RESULTS = 3

# Vector DB
CHROMA_COLLECTION_NAME = "study_notes"

# File upload
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = [
    ".pdf", ".txt",
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"
]