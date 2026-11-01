"""
core/tts.py — Text to Speech Engine
===================================
Generates spoken audio from text using gTTS (Google Text-to-Speech)
Supports English, Hindi, Marathi, Spanish, French, German.
"""

import io
from typing import Optional


def text_to_speech_bytes(text: str, lang: str = "en") -> bytes:
    """
    Converts input text into MP3 audio bytes.
    lang code mapping:
      'en' -> English
      'hi' -> Hindi
      'mr' -> Marathi
      'es' -> Spanish
      'fr' -> French
      'de' -> German
    """
    from gtts import gTTS

    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Cannot synthesize audio: text is empty.")

    # Standardize lang codes
    code = "en"
    lang_lower = lang.lower()
    if "hi" in lang_lower:
        code = "hi"
    elif "mr" in lang_lower:
        code = "mr"
    elif "es" in lang_lower:
        code = "es"
    elif "fr" in lang_lower:
        code = "fr"
    elif "de" in lang_lower:
        code = "de"

    buf = io.BytesIO()
    tts = gTTS(text=cleaned, lang=code)
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.getvalue()
