"""
ParkinSense 2.0 — Handwriting → Text → Voice page
Run:  streamlit run handwriting_app.py
"""
import json

import cv2
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

from handwriting import analyze, analyze_with_validation, load_image_from_bytes, text_to_speech_bytes


def get_upload_key(upload, photo):
    if upload is not None:
        return ("upload", getattr(upload, "name", ""), getattr(upload, "size", 0))
    if photo is not None:
        return ("photo", getattr(photo, "name", ""), getattr(photo, "size", 0))
    return None


def should_process_new_image(upload, photo, session_state):
    current_key = get_upload_key(upload, photo)
    last_key = session_state.get("last_upload_key")
    return current_key is not None and current_key != last_key


def browser_speak(text: str, lang_tag: str = "en-US"):
    """Backup voice: the browser's built-in speechSynthesis (offline, free)."""
    payload = json.dumps({"text": text, "lang": lang_tag})
    components.html(
        f"""<script>
            const data = {payload};
            const u = new SpeechSynthesisUtterance(data.text);
            u.lang = data.lang;
            u.rate = 0.95;
            speechSynthesis.cancel();
            speechSynthesis.speak(u);
        </script>""",
        height=0,
    )


def draw_boxes(gray_img, results):
    """Green = confident word, orange = unsure, red = probably wrong."""
    canvas = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
    for bbox, _t, conf in results:
        pts = np.array(bbox, dtype=np.int32).reshape(-1, 1, 2)
        color = (0, 180, 0) if conf >= 0.8 else (0, 160, 255) if conf >= 0.5 else (0, 0, 255)
        cv2.polylines(canvas, [pts], True, color, 2)
    return canvas


def to_rgb(img):
    """Convert any OpenCV image (grayscale / BGR / BGRA) to RGB for st.image."""
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    if img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def run_ocr_for_image(raw, lang_code, enhance, current_key=None,
                     engine="trocr", trocr_model="microsoft/trocr-base-handwritten",
                     num_beams=5, white_bg=True, spell_correct=True,
                     validator="easyocr", min_confidence=0.72, gemini_api_key=None):
    if raw is None:
        return None

    try:
        img_bgr = load_image_from_bytes(raw)
        with st.spinner("Reading the handwriting… (first run downloads the model, ~100 MB, once)"):
            if engine == "fusion":
                work_img, results, text, source, confidence = analyze_with_validation(
                    img_bgr,
                    raw_bytes=raw,
                    languages=lang_code,
                    enhance=enhance,
                    trocr_model=trocr_model,
                    num_beams=num_beams,
                    white_bg=white_bg,
                    spell_correct=spell_correct,
                    validator=validator,
                    min_confidence=min_confidence,
                    gemini_api_key=gemini_api_key,
                )
                if source != "trocr":
                    st.info(f"Low-confidence TrOCR result; re-ran with {source.upper()} validator.")
            else:
                work_img, results, text = analyze(
                    img_bgr,
                    lang_code,
                    enhance=enhance,
                    engine=engine,
                    trocr_model=trocr_model,
                    num_beams=num_beams,
                    white_bg=white_bg,
                    spell_correct=spell_correct,
                )
                source, confidence = engine, 0.0
    except Exception as e:
        st.error(f"OCR failed: {e}")
        return None

    st.session_state["results"] = results
    st.session_state["enhanced"] = work_img
    st.session_state["raw_text"] = text
    st.session_state["img_bgr"] = img_bgr
    st.session_state["ocr_source"] = source
    st.session_state["ocr_confidence"] = confidence
    st.session_state.pop("transcript", None)
    if current_key is not None:
        st.session_state["last_upload_key"] = current_key
    return img_bgr


def main():
    st.set_page_config(page_title="ParkinSense — Handwriting to Text",
                       page_icon="✍️", layout="wide")

    st.title("✍️ Handwriting → Text → Voice")
    st.caption("ParkinSense 2.0 · Upload or photograph a handwritten page — "
               "we read it out loud so it can be heard, not just seen.")

    # ---------------- Sidebar settings ----------------
    with st.sidebar:
        st.header("⚙️ Settings")
        engine = st.radio("Reading mode",
                          ["🧠 TrOCR — best accuracy (English cursive)",
                           "🚀 EasyOCR — fast (needed for Hindi)",
                           "🛡️ Fusion — TrOCR + validator"])
        use_trocr = engine.startswith("🧠")
        use_fusion = engine.startswith("🛡️")
        validator_choice = st.radio("Validator", ["EasyOCR", "Gemini"], index=0,
                                   help="When TrOCR confidence is low, re-run with the chosen validator.") if use_fusion else "easyocr"
        gemini_api_key = st.text_input("Gemini API key", type="password",
                                       help="Only needed for the Gemini validator.") if use_fusion and validator_choice == "Gemini" else None
        if use_trocr or use_fusion:
            size = st.selectbox("TrOCR model size", index=1,
                                options=["base (smaller download)",
                                         "large (≈2 GB download, best accuracy)"])
            trocr_model = ("microsoft/trocr-large-handwritten" if size.startswith("large")
                           else "microsoft/trocr-base-handwritten")
            num_beams = st.slider("Recognition quality (beam width)", 2, 8, 5)
            white_bg = st.checkbox("Force white background (helps shaded photos)", value=True)
            spell_fix = st.checkbox("Auto-fix spelling (English only)", value=True)
            min_confidence = st.slider("Low-confidence re-run threshold", 0.50, 0.95, 0.72, step=0.01)
        else:
            trocr_model, num_beams = "microsoft/trocr-base-handwritten", 5
            white_bg, spell_fix = True, True
            min_confidence = 0.72

        lang_name = st.selectbox("Writing language",
                                 ["English", "Hindi", "Hindi + English"],
                                 disabled=use_trocr or use_fusion,
                                 help="TrOCR is English-only; switch to EasyOCR or use fusion for Hindi.")
        LANG_CODES = {"English": ("en",), "Hindi": ("hi",), "Hindi + English": ("hi", "en")}
        TTS_CODES  = {"English": "en",      "Hindi": "hi",      "Hindi + English": "hi"}
        TTS_TAGS   = {"English": "en-US",   "Hindi": "hi-IN",   "Hindi + English": "hi-IN"}
        enhance    = st.checkbox("Enhance photo before reading", value=True)
        show_boxes = st.checkbox("Show what the model saw", value=True)

    # ---------------- Input: upload or camera ----------------
    upload = st.file_uploader("Upload a handwritten page",
                              type=["png", "jpg", "jpeg", "bmp", "webp"])
    photo = st.camera_input("…or take a photo of the page right now")

    raw = upload.getvalue() if upload is not None else (photo.getvalue() if photo is not None else None)
    if raw is None:
        st.info("👆 Upload a photo of the handwritten page, or take one with the camera, to begin.")
        st.stop()

    current_key = get_upload_key(upload, photo)
    if should_process_new_image(upload, photo, st.session_state):
        img_bgr = run_ocr_for_image(
            raw,
            LANG_CODES[lang_name],
            enhance,
            current_key=current_key,
            engine="trocr" if use_trocr else "easyocr" if not use_fusion else "fusion",
            trocr_model=trocr_model,
            num_beams=num_beams,
            white_bg=white_bg,
            spell_correct=spell_fix,
            validator=validator_choice.lower(),
            min_confidence=min_confidence,
            gemini_api_key=gemini_api_key,
        )
    else:
        img_bgr = st.session_state.get("img_bgr")

    try:
        if img_bgr is None and raw is not None:
            img_bgr = load_image_from_bytes(raw)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    left, right = st.columns(2)
    with left:
        st.markdown("**Original**")
        st.image(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), use_container_width=True)

    # ---------------- Run OCR ----------------
    if st.button("🔎 Read my writing", type="primary"):
        run_ocr_for_image(
            raw,
            LANG_CODES[lang_name],
            enhance,
            current_key=current_key,
            engine="trocr" if use_trocr else "easyocr" if not use_fusion else "fusion",
            trocr_model=trocr_model,
            num_beams=num_beams,
            white_bg=white_bg,
            spell_correct=spell_fix,
            validator=validator_choice.lower(),
            min_confidence=min_confidence,
            gemini_api_key=gemini_api_key,
        )

    # ---------------- Show results ----------------
    if "results" in st.session_state:
        results = st.session_state["results"]

        if not results:
            st.warning("I couldn't find readable writing. Try: better lighting, camera held "
                       "flat above the page, text filling most of the frame.")
        else:
            n_chars = sum(len(t) for _, t, _ in results) or 1
            avg_conf = sum(c * len(t) for _, t, c in results) / n_chars
            if avg_conf >= 0.90:
                st.success(f"Estimated reading confidence: **{avg_conf:.0%}** — strong read.")
            elif avg_conf >= 0.75:
                st.warning(f"Estimated reading confidence: **{avg_conf:.0%}** — please skim the text.")
            else:
                st.error(f"Estimated reading confidence: **{avg_conf:.0%}** — please review carefully.")

            with st.expander("What this number means"):
                st.caption("This is the model's own certainty, lightly rescaled — not measured "
                           "accuracy. For real accuracy, run evaluate_cer.py on pages where you "
                           "know the true text. CER ≤ 10% means >90% accuracy, and that's the "
                           "number for your report.")

            left, right = st.columns(2)
            with left:
                st.markdown("**What the model saw** (green = sure, red = unsure)")
                shown = draw_boxes(st.session_state["enhanced"], results) if show_boxes \
                        else st.session_state["enhanced"]
                st.image(to_rgb(shown), use_container_width=True)

            with right:
                st.markdown("**Transcription** — fix any mistakes before it speaks 👇")
                final_text = st.text_area("Transcript", value=st.session_state["raw_text"],
                                          height=280, label_visibility="collapsed")

            # ---------------- Audio output ----------------
            st.divider()
            st.subheader("🔊 Hear what they want to say")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("▶️ Speak (online voice)", disabled=not final_text.strip()):
                    try:
                        st.session_state["audio"] = text_to_speech_bytes(final_text, TTS_CODES[lang_name])
                    except Exception:
                        st.warning("Online voice failed (needs internet) — use the browser voice →")
            with b2:
                if st.button("🗣️ Speak (browser voice)", disabled=not final_text.strip()):
                    browser_speak(final_text, TTS_TAGS[lang_name])

            if st.session_state.get("audio"):
                try:
                    st.audio(st.session_state["audio"], format="audio/mp3", autoplay=True)
                except TypeError:  # older Streamlit: no autoplay param
                    st.audio(st.session_state["audio"], format="audio/mp3")


if __name__ == "__main__":
    main()