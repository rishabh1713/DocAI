import numpy as np
from PIL import Image

_reader = None


def _get_reader():
    """Initialize EasyOCR reader once and reuse."""
    global _reader
    if _reader is None:
        try:
            import easyocr
            _reader = easyocr.Reader(['en'], gpu=False)
        except ImportError:
            raise RuntimeError(
                "EasyOCR is not installed. Run: pip install easyocr"
            )
    return _reader


def extract_text_from_image(image_path: str) -> str:
    """Extract text from an image file using EasyOCR."""
    try:
        image = Image.open(image_path)
    except Exception as e:
        raise RuntimeError(f"Could not open image: {e}")

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    image_array = np.array(image)

    reader = _get_reader()
    results = reader.readtext(image_array)

    if not results:
        raise ValueError("No text found in image. Use a clearer photo.")

    return " ".join([result[1] for result in results]).strip()