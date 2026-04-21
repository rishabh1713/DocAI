import os
import shutil
from pathlib import Path
from config.settings import UPLOAD_DIR, ALLOWED_EXTENSIONS


def save_uploaded_file(uploaded_file) -> str:
    """Save Streamlit uploaded file to disk. Returns saved file path."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_ext = Path(uploaded_file.name).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {file_ext}. Allowed: {ALLOWED_EXTENSIONS}"
        )

    save_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(uploaded_file, f)

    return save_path


def delete_file(file_path: str):
    """Delete a file from disk if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)