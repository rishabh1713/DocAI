import io
import fitz
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb

from config.settings import CHUNK_SIZE, CHUNK_OVERLAP, CHROMA_COLLECTION_NAME
from utils.file_handler import is_image_file
from services.vision_ocr_service import extract_text_from_image_fast  # ← changed
from services.ocr_service import extract_text_from_image

# Lower DPI since Groq Vision handles quality on their end
DPI = 120
MAX_WORKERS = 6
MIN_CHARS_TO_SKIP_OCR = 100


def _pdf_page_to_pil(page) -> Image.Image:
    """Render a PDF page to PIL Image."""
    zoom = DPI / 72
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    image_bytes = pixmap.tobytes("png")
    return Image.open(io.BytesIO(image_bytes))


def _process_single_page(args) -> str:
    """
    Process one PDF page.
    Text pages  → direct extraction (instant, no API call)
    Image pages → Groq Vision API (fast, free)
    Mixed pages → both combined
    """
    page_number, file_path = args
    page_text = ""

    try:
        pdf = fitz.open(file_path)
        page = pdf[page_number]
        page_label = f"[Page {page_number + 1}]"

        direct_text = page.get_text("text").strip()
        has_enough_text = len(direct_text) >= MIN_CHARS_TO_SKIP_OCR
        has_images = len(page.get_images(full=True)) > 0

        if has_enough_text and not has_images:
            # Pure text page — no API call needed at all
            page_text = f"\n{page_label}\n{direct_text}\n"

        elif has_enough_text and has_images:
            # Mixed — keep direct text + OCR the image parts
            page_text = f"\n{page_label}\n{direct_text}\n"
            pil_image = _pdf_page_to_pil(page)
            ocr_text = extract_text_from_image_fast(pil_image)
            if ocr_text:
                page_text += f"\n{page_label} (image OCR):\n{ocr_text}\n"

        else:
            # Image-only page — full Groq Vision OCR
            pil_image = _pdf_page_to_pil(page)
            ocr_text = extract_text_from_image_fast(pil_image)
            if ocr_text:
                page_text = f"\n{page_label} (OCR):\n{ocr_text}\n"
            elif direct_text:
                page_text = f"\n{page_label}\n{direct_text}\n"

        pdf.close()

    except Exception as e:
        print(f"Warning: could not process page {page_number + 1}: {e}")

    return page_text


def _extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from PDF using parallel Groq Vision OCR."""
    temp_pdf = fitz.open(file_path)
    total_pages = len(temp_pdf)
    temp_pdf.close()

    page_args = [(i, file_path) for i in range(total_pages)]
    page_results = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {
            executor.submit(_process_single_page, args): args[0]
            for args in page_args
        }
        for future in as_completed(future_to_page):
            page_number = future_to_page[future]
            try:
                page_results[page_number] = future.result()
            except Exception as e:
                print(f"Page {page_number + 1} failed: {e}")
                page_results[page_number] = ""

    return "".join(page_results.get(i, "") for i in range(total_pages))


def _extract_text(file_path: str) -> str:
    """Route to correct extractor based on file type."""
    if file_path.lower().endswith(".pdf"):
        return _extract_text_from_pdf(file_path)
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


def ingest_file(file_path: str) -> int:
    """Full pipeline: file → extract → chunk → store."""
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