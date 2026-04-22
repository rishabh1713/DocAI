from PIL import Image
from services.vision_ocr_service import extract_text_from_image_fast


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from a standalone image file.
    Now uses Groq Vision instead of EasyOCR — faster and free.
    """
    try:
        pil_image = Image.open(image_path)
        if pil_image.mode not in ("RGB", "L"):
            pil_image = pil_image.convert("RGB")
        return extract_text_from_image_fast(pil_image)
    except Exception as e:
        raise RuntimeError(f"Image OCR failed: {e}")