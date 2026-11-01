"""Run:  streamlit run handwriting_app_cloud.py"""
import io
import json

import streamlit as st
import streamlit.components.v1 as components

from handwriting_cloud import read_handwriting_bytes

st.set_page_config(page_title="ParkinSense — Handwriting to Text", page_icon="✍️", layout="wide")
st.title("✍️ Handwriting → Text → Voice")
st.caption("Upload or photograph a handwritten page — one tap to hear it spoken.")

# ---------- Sidebar ----------
try:
    default_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    default_key = ""
with st.sidebar:
    api_key = st.text_input("Gemini API key", value=default_key, type="password",
                            help="Free key: https://aistudio.google.com/apikey")
    lang = st.selectbox("Voice language", ["English", "Hindi", "Marathi"])
    use_browser_voice = st.checkbox("Use browser voice (works offline)", value=False)

TTS = {"English": ("en", "en-US"), "Hindi": ("hi", "hi-IN"), "Marathi": ("mr", "mr-IN")}


def browser_speak(text, tag):
    components.html(f"""<script>
        const u = new SpeechSynthesisUtterance({json.dumps(text)});
        u.lang = {json.dumps(tag)}; u.rate = 0.95;
        speechSynthesis.cancel(); speechSynthesis.speak(u);
    </script>""", height=0)


def gtts_bytes(text, code):
    from gtts import gTTS
    buf = io.BytesIO()
    gTTS(text=text, lang=code).write_to_fp(buf)
    buf.seek(0)
    return buf.getvalue()


# ---------- Input ----------
upload = st.file_uploader("Upload a page", type=["png", "jpg", "jpeg", "webp", "bmp"])
photo = st.camera_input("…or take a photo right now")
raw = upload.getvalue() if upload is not None else (photo.getvalue() if photo is not None else None)

if raw is None:
    st.info("👆 Upload or photograph a page to begin.")
    st.stop()

st.image(upload if upload is not None else photo, use_container_width=True)

# ---------- Transcribe ----------
if st.button("🔎 Read my writing", type="primary"):
    if not api_key.strip():
        st.error("Paste your free Gemini API key in the sidebar first.")
        st.stop()
    with st.spinner("Reading…"):
        try:
            text = read_handwriting_bytes(raw, mime=(upload.type if upload is not None else "image/jpeg"),
                                          api_key=api_key.strip())
        except Exception as e:
            st.error(f"Could not read the page: {e}")
            st.stop()
    st.session_state["raw"] = text

# ---------- Output ----------
if "raw" in st.session_state:
    st.subheader("📝 Transcription")
    final = st.text_area("Check and fix anything wrong before it speaks",
                         value=st.session_state["raw"], height=250,
                         label_visibility="collapsed")
    if st.button("🔊 Hear it", type="primary", disabled=not final.strip()):
        code, tag = TTS[lang]
        if use_browser_voice:
            browser_speak(final, tag)
        else:
            try:
                st.audio(gtts_bytes(final, code), format="audio/mp3", autoplay=True)
            except TypeError:
                st.audio(gtts_bytes(final, code), format="audio/mp3")
