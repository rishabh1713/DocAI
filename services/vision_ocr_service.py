import base64
import io
from PIL import Image
from groq import Groq
from config.settings import GROQ_API_KEY

# Initialize Groq client once
client = Groq(api_key=GROQ_API_KEY)

# Groq's free vision model
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def _image_to_base64(pil_image: Image.Image) -> str:
    """Convert PIL image to base64 string."""
    buffer = io.BytesIO()

    if pil_image.mode not in ("RGB", "L"):
        pil_image = pil_image.convert("RGB")

    # Resize if image is too large — keeps API calls fast
    max_size = 1024
    if pil_image.width > max_size or pil_image.height > max_size:
        pil_image.thumbnail((max_size, max_size))

    pil_image.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def extract_text_from_image_fast(pil_image: Image.Image) -> str:
    """
    Send image to Groq Vision API and get all text back.
    Uses your existing Groq API key — completely free.
    """
    try:
        image_b64 = _image_to_base64(pil_image)

        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                "Extract ALL text from this image exactly as it appears. "
                                "Include text from diagrams, tables, figures, and captions. "
                                "Do not summarize — just output the raw extracted text only."
                            )
                        }
                    ]
                }
            ],
            max_tokens=2048
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        raise RuntimeError(f"Groq Vision OCR failed: {e}")