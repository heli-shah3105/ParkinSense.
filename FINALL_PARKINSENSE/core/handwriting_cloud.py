"""
handwriting_cloud.py — simplest handwriting → text for ParkinSense 2.0.
One Gemini API call replaces the entire local OCR pipeline.

Glue-code functions (same signatures the lead's app.py already expects):
    read_handwriting(image_path) -> str
    read_handwriting_bytes(raw_bytes) -> str
"""
import os
from pathlib import Path

from google import genai
from google.genai import types

MODEL = "gemini-2.0-flash"

PROMPT = (
    "You are transcribing a page of shaky handwriting from a person with a "
    "hand tremor so they can communicate. Rules:\n"
    "1. Transcribe EXACTLY what is written — preserve the line breaks.\n"
    "2. Use context to give your best reading of shaky or unclear words.\n"
    "3. If a word is truly unreadable, write your best guess followed by [?].\n"
    "4. Never invent sentences that are not on the page.\n"
    "5. Output ONLY the transcription — no commentary, no markdown."
)

_client = None


def _get_client(api_key=None):
    global _client
    if _client is None:
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "No Gemini API key. Get a free one at https://aistudio.google.com/apikey "
                "and paste it into the sidebar (or set GEMINI_API_KEY).")
        _client = genai.Client(api_key=key)
    return _client


def read_handwriting_bytes(raw: bytes, mime: str = "image/jpeg",
                          api_key=None, model: str = MODEL) -> str:
    """★ Image bytes in → full transcript string out. That's the whole pipeline."""
    client = _get_client(api_key)
    resp = client.models.generate_content(
        model=model,
        contents=[types.Part.from_bytes(data=raw, mime_type=mime), PROMPT],
    )
    return (resp.text or "").strip()


def read_handwriting(image_path, api_key=None, model: str = MODEL) -> str:
    """★ File path in → transcript out."""
    p = Path(image_path)
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".bmp": "image/bmp"}.get(p.suffix.lower(), "image/jpeg")
    return read_handwriting_bytes(p.read_bytes(), mime=mime, api_key=api_key, model=model)
