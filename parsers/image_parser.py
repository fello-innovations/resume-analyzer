import base64
from openai import OpenAI
from config import TOGETHER_API_KEY, TOGETHER_BASE_URL, LLM_VISION_MODEL, IMAGE_BATCH_SIZE


class ImageParser:
    """
    Extracts text from image-based PDF pages using a vision LLM.
    Pages are sent in batches of IMAGE_BATCH_SIZE.
    """

    def __init__(self):
        self._client = OpenAI(
            api_key=TOGETHER_API_KEY,
            base_url=TOGETHER_BASE_URL,
        )

    def extract_text_from_images(self, page_images: list[bytes]) -> str:
        """Send page images to vision LLM and return concatenated text."""
        all_text = []
        for i in range(0, len(page_images), IMAGE_BATCH_SIZE):
            batch = page_images[i : i + IMAGE_BATCH_SIZE]
            text = self._process_batch(batch)
            all_text.append(text)
        return "\n".join(all_text)

    def _process_batch(self, images: list[bytes]) -> str:
        content = [
            {
                "type": "text",
                "text": (
                    "You are an OCR assistant. Extract ALL text from the following resume page images. "
                    "Output only the extracted text, preserving structure where possible. "
                    "Do not add commentary."
                ),
            }
        ]
        for img_bytes in images:
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            })

        response = self._client.chat.completions.create(
            model=LLM_VISION_MODEL,
            messages=[{"role": "user", "content": content}],
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""
