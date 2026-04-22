import io
import time
import fitz
from PIL import Image
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb

from config.settings import CHUNK_SIZE, CHUNK_OVERLAP, CHROMA_COLLECTION_NAME
from utils.file_handler import is_image_file
from services.vision_ocr_service import extract_text_from_image_fast
from services.ocr_service import extract_text_from_image

# ── Tuning constants ──────────────────────────────────────────────────────────
DPI = 120                # lower = faster rendering, still readable
MIN_CHARS_TO_SKIP_OCR = 100   # pages with more chars than this skip OCR
BATCH_SIZE = 10          # process 10 pages at a time
RATE_LIMIT_DELAY = 2     # seconds to wait between batches


def _pdf_page_to_pil(page) -> Image.Image:
    """Render a PDF page to PIL image."""
    zoom = DPI / 72
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    return Image.open(io.BytesIO(pixmap.tobytes("png")))


def _is_image_only_page(page) -> bool:
    """Return True if page has no selectable text — needs OCR."""
    direct_text = page.get_text("text").strip()
    return len(direct_text) < MIN_CHARS_TO_SKIP_OCR


def _process_single_page(page, page_number: int) -> str:
    """
    Process one page smartly:
    - Text page  → direct extract, zero API calls
    - Image page → Groq Vision OCR
    - Mixed page → direct text + OCR for image content
    """
    page_label = f"[Page {page_number + 1}]"
    direct_text = page.get_text("text").strip()
    has_images = len(page.get_images(full=True)) > 0
    has_enough_text = len(direct_text) >= MIN_CHARS_TO_SKIP_OCR

    try:
        if has_enough_text and not has_images:
            # ── Pure text page — fastest path, no API call ────────
            return f"\n{page_label}\n{direct_text}\n"

        elif has_enough_text and has_images:
            # ── Mixed page — text + OCR for image parts ───────────
            pil_image = _pdf_page_to_pil(page)
            ocr_text = extract_text_from_image_fast(pil_image)
            result = f"\n{page_label}\n{direct_text}\n"
            if ocr_text:
                result += f"\n{page_label} (image OCR):\n{ocr_text}\n"
            return result

        else:
            # ── Image-only page — full OCR ─────────────────────────
            pil_image = _pdf_page_to_pil(page)
            ocr_text = extract_text_from_image_fast(pil_image)
            if ocr_text:
                return f"\n{page_label} (OCR):\n{ocr_text}\n"
            elif direct_text:
                return f"\n{page_label}\n{direct_text}\n"
            return ""

    except Exception as e:
        print(f"Warning: page {page_number + 1} failed: {e}")
        # fallback — return whatever direct text we have
        return f"\n{page_label}\n{direct_text}\n" if direct_text else ""


def _extract_text_from_pdf(file_path: str, progress_callback=None) -> str:
    """
    Extract all text from PDF with:
    - Smart OCR skipping for text pages
    - Batch processing with rate limit delays
    - Live progress updates
    """
    pdf_document = fitz.open(file_path)
    total_pages = len(pdf_document)
    full_text = ""

    # Count how many pages actually need OCR
    image_pages = sum(
        1 for i in range(total_pages)
        if _is_image_only_page(pdf_document[i])
    )
    text_pages = total_pages - image_pages

    print(f"PDF has {total_pages} pages: {text_pages} text, {image_pages} need OCR")

    # Process in batches to avoid rate limits
    for batch_start in range(0, total_pages, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_pages)
        batch_pages = range(batch_start, batch_end)

        # Update progress
        progress = int((batch_start / total_pages) * 100)
        if progress_callback:
            progress_callback(
                progress,
                f"Processing pages {batch_start + 1}–{batch_end} of {total_pages}..."
            )

        # Process each page in this batch
        for page_number in batch_pages:
            page = pdf_document[page_number]
            page_text = _process_single_page(page, page_number)
            full_text += page_text

        # Wait between batches ONLY if next batch has OCR pages
        # (no need to wait if all remaining pages are text)
        if batch_end < total_pages:
            next_batch_has_ocr = any(
                _is_image_only_page(pdf_document[i])
                for i in range(batch_end, min(batch_end + BATCH_SIZE, total_pages))
            )
            if next_batch_has_ocr:
                time.sleep(RATE_LIMIT_DELAY)

    pdf_document.close()

    if progress_callback:
        progress_callback(100, "Extraction complete!")

    return full_text


def _extract_text(file_path: str, progress_callback=None) -> str:
    """Route to correct extractor based on file type."""
    if file_path.lower().endswith(".pdf"):
        return _extract_text_from_pdf(file_path, progress_callback)
    elif is_image_file(file_path):
        return extract_text_from_image(file_path)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_text(text)


def ingest_file(file_path: str, progress_callback=None) -> int:
    """
    Full pipeline: file → extract → chunk → store.
    progress_callback(percent, message) is called during PDF processing.
    Returns number of chunks stored.
    """
    text = _extract_text(file_path, progress_callback)

    if not text.strip():
        raise ValueError("No text could be extracted from the file.")

    chunks = _chunk_text(text)

    client = chromadb.Client()
    collection = client.get_or_create_collection(CHROMA_COLLECTION_NAME)

    # Clear old data first to avoid ID conflicts on retry
    try:
        existing = collection.get()
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))],
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