"""
handwriting.py — ParkinSense 2.0 (Member B) core module
=======================================================
Image in → text out → audio out. No Streamlit here, so app.py,
Colab notebooks, and test scripts can import it directly.

Glue-code functions (the signatures the lead's app.py will call):
    read_handwriting(image_path, languages=("en",), enhance=True) -> str
    read_handwriting_bytes(raw_bytes, languages=("en",), enhance=True) -> str
    text_to_speech_bytes(text, lang="en") -> bytes   # mp3 audio
    cer(reference_text, hypothesis_text) -> float    # Weeks 9–10 metric
"""

import io
from pathlib import Path

import cv2
import numpy as np

# --------------------------------------------------------------------------
# 1. Image loading
# --------------------------------------------------------------------------
def load_image(path) -> np.ndarray:
    """Read an image from disk (handles unicode paths on Windows)."""
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not read image: {path}")
    return img


def load_image_from_bytes(raw: bytes) -> np.ndarray:
    """Read an image from raw bytes (e.g. a Streamlit upload)."""
    img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image — is it a valid png/jpg?")
    return img


# --------------------------------------------------------------------------
# 2. Preprocessing — gives shaky handwriting its best chance
# --------------------------------------------------------------------------
def preprocess(img_bgr: np.ndarray) -> np.ndarray:
    h, w = img_bgr.shape[:2]

    # Cap resolution — huge phone photos are slow and add noise
    scale = 2000 / max(h, w)
    if scale < 1:
        img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)),
                             interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Smooth pen jitter, paper texture, photo grain
    gray = cv2.fastNlMeansDenoising(gray, h=15)

    # Darken faint strokes, flatten bad lighting
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    return gray


# --------------------------------------------------------------------------
# 3. OCR engine (cached — loads once per process)
# --------------------------------------------------------------------------
_READERS = {}

def get_reader(lang_codes, gpu=False):
    key = tuple(sorted(lang_codes))
    if key not in _READERS:
        import easyocr  # slow import — only when actually needed
        _READERS[key] = easyocr.Reader(list(key), gpu=gpu)
    return _READERS[key]


# --------------------------------------------------------------------------
# 4. Detection → readable text (group word boxes into lines)
# --------------------------------------------------------------------------
def _detections_to_text(results) -> str:
    items = []
    for bbox, text, conf in results:
        text = text.strip()
        if not text:
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        items.append({"text": text, "conf": float(conf),
                      "x0": min(xs), "yc": (min(ys) + max(ys)) / 2,
                      "h": max(ys) - min(ys)})
    if not items:
        return ""

    med_h = sorted(it["h"] for it in items)[len(items) // 2] or 20.0
    items.sort(key=lambda it: it["yc"])

    # Split into lines whenever the y-centre jumps ~one text height
    lines = [[items[0]]]
    for it in items[1:]:
        if abs(it["yc"] - lines[-1][-1]["yc"]) <= med_h * 0.8:
            lines[-1].append(it)
        else:
            lines.append([it])

    text_lines = []
    for line in lines:
        line.sort(key=lambda it: it["x0"])          # left → right
        text_lines.append(" ".join(it["text"] for it in line))
    return "\n".join(text_lines)


# --------------------------------------------------------------------------
# 3b. TrOCR engine — EasyOCR finds lines, TrOCR reads them
# --------------------------------------------------------------------------
_TROCR = {}
MAX_CHUNK_ASPECT = 8.0


def _get_trocr(model_name="microsoft/trocr-base-handwritten"):
    if model_name not in _TROCR:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        proc = TrOCRProcessor.from_pretrained(model_name)
        model = VisionEncoderDecoderModel.from_pretrained(model_name)
        model.eval()
        _TROCR[model_name] = (proc, model)
    return _TROCR[model_name]


def _white_background(gray):
    """Otsu binarization: ink -> black, paper -> clean white (kills shadows)."""
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return bw


def _group_chunks(results):
    """Group EasyOCR word boxes into lines, then split wide lines into
    chunks with aspect ratio <= 8 so TrOCR never sees squashed text."""
    items = []
    for bbox, text, _c in results:
        if not text.strip():
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        items.append({"x0": min(xs), "x1": max(xs), "y0": min(ys), "y1": max(ys),
                      "yc": (min(ys) + max(ys)) / 2, "h": max(ys) - min(ys)})
    if not items:
        return []
    med_h = sorted(i["h"] for i in items)[len(items) // 2] or 20.0
    items.sort(key=lambda i: i["yc"])
    lines = [[items[0]]]
    for it in items[1:]:
        if abs(it["yc"] - lines[-1][-1]["yc"]) <= med_h * 0.8:
            lines[-1].append(it)
        else:
            lines.append([it])

    chunks = []
    for ln in lines:
        ln.sort(key=lambda i: i["x0"])
        y0 = int(min(i["y0"] for i in ln))
        y1 = int(max(i["y1"] for i in ln))
        h = max(1.0, y1 - y0)
        cur = [ln[0]]
        for w in ln[1:]:
            if (cur[-1]["x1"] - cur[0]["x0"]) / h >= MAX_CHUNK_ASPECT:
                chunks.append((int(cur[0]["x0"]), y0, int(cur[-1]["x1"]), y1))
                cur = [w]
            else:
                cur.append(w)
        if cur:
            chunks.append((int(cur[0]["x0"]), y0, int(cur[-1]["x1"]), y1))
    return chunks


def _recognize_lines_trocr(work, chunk_boxes,
                           model_name="microsoft/trocr-base-handwritten",
                           num_beams=5, white_bg=True):
    import torch
    proc, model = _get_trocr(model_name)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    src = work if work.ndim == 2 else cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)

    out = []
    for (x0, y0, x1, y1) in chunk_boxes:
        pad_y = max(8, int(0.4 * (y1 - y0)))
        pad_x = max(8, int(0.15 * (y1 - y0)))
        ya, yb = max(0, y0 - pad_y), min(src.shape[0], y1 + pad_y)
        xa, xb = max(0, x0 - pad_x), min(src.shape[1], x1 + pad_x)
        crop = src[ya:yb, xa:xb]
        if crop.size == 0 or crop.shape[0] < 10 or crop.shape[1] < 20:
            continue
        if white_bg:
            crop = _white_background(crop)
        rgb = cv2.cvtColor(crop, cv2.COLOR_GRAY2RGB)
        px = proc(images=rgb, return_tensors="pt").pixel_values.to(device)
        with torch.inference_mode():
            gen = model.generate(px, num_beams=num_beams, max_new_tokens=128,
                                 return_dict_in_generate=True, output_scores=True)
        text = proc.batch_decode(gen.sequences, skip_special_tokens=True)[0].strip()
        conf = 0.5
        if getattr(gen, "sequences_scores", None) is not None:
            raw = float(torch.exp(gen.sequences_scores[0]))
            conf = min(0.98, max(0.05, raw ** 0.4))
        if text:
            out.append(([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], text, conf))
    return out


def postprocess_text(text, enabled=True):
    """Dictionary-based spelling fix for OCR slips (e.g. 'writng' -> 'writing')."""
    if not enabled or not text.strip():
        return text
    try:
        from spellchecker import SpellChecker
    except ImportError:
        return text
    spell = SpellChecker()
    fixed_lines = []
    for line in text.splitlines():
        out = []
        for w in line.split():
            core = "".join(ch for ch in w if ch.isalpha())
            if len(core) >= 3 and core.lower() not in spell:
                c = spell.correction(core)
                if c and core[0].isupper():
                    c = c[0].upper() + c[1:]
                if c:
                    w = w.replace(core, c)
            out.append(w)
        fixed_lines.append(" ".join(out))
    return "\n".join(fixed_lines)


def confidence_from_results(results) -> float:
    """Average confidence across OCR results, weighted by text length."""
    if not results:
        return 0.0
    total_chars = sum(len(text) for _, text, _ in results) or 1
    weighted = sum(conf * len(text) for _, text, conf in results)
    return weighted / total_chars


def _should_retry_with_validator(primary_text: str, primary_conf: float, min_confidence: float) -> bool:
    text = (primary_text or "").strip()
    short_text = len(text) < 20 or len(text.split()) < 3
    return not text or short_text or primary_conf < min_confidence


def analyze_with_validation(img_bgr, raw_bytes=None, languages=("en",), enhance=True,
                           gpu=False, validator="easyocr", min_confidence=0.72,
                           trocr_model="microsoft/trocr-base-handwritten",
                           num_beams=5, white_bg=True, spell_correct=True,
                           gemini_api_key=None):
    """TrOCR primary, secondary validator fallback when the confidence is low or the transcript is incomplete."""
    primary_work, primary_results, primary_text = analyze(
        img_bgr,
        languages=languages,
        enhance=enhance,
        gpu=gpu,
        engine="trocr",
        trocr_model=trocr_model,
        num_beams=num_beams,
        white_bg=white_bg,
        spell_correct=spell_correct,
    )
    primary_conf = confidence_from_results(primary_results)
    if not _should_retry_with_validator(primary_text, primary_conf, min_confidence):
        return primary_work, primary_results, primary_text, "trocr", primary_conf

    validator_name = (validator or "easyocr").lower()
    if validator_name == "easyocr":
        val_work, val_results, val_text = analyze(
            img_bgr,
            languages=languages,
            enhance=enhance,
            gpu=gpu,
            engine="easyocr",
            trocr_model=trocr_model,
            num_beams=num_beams,
            white_bg=white_bg,
            spell_correct=spell_correct,
        )
        val_conf = confidence_from_results(val_results)
        chosen = val_text if len((val_text or "").strip()) >= len((primary_text or "").strip()) else primary_text
        return (val_work, val_results, chosen, "easyocr", val_conf) if len((val_text or "").strip()) >= len((primary_text or "").strip()) else (primary_work, primary_results, primary_text, "trocr", primary_conf)

    if validator_name == "gemini":
        if raw_bytes is None:
            raise ValueError("Gemini validation needs the original raw image bytes.")
        from handwriting_cloud import read_handwriting_bytes
        mime = "image/jpeg"
        val_text = read_handwriting_bytes(raw_bytes, mime=mime, api_key=gemini_api_key)
        chosen = val_text if len((val_text or "").strip()) >= len((primary_text or "").strip()) else primary_text
        return primary_work, primary_results, chosen, "gemini", primary_conf

    return primary_work, primary_results, primary_text, "trocr", primary_conf


def analyze(img_bgr, languages=("en",), enhance=True, gpu=False,
            engine="trocr", trocr_model="microsoft/trocr-base-handwritten",
            num_beams=5, white_bg=True, spell_correct=True):
    """Run the full OCR pipeline on an image array."""
    work = preprocess(img_bgr) if enhance else cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    reader = get_reader(languages, gpu=gpu)
    detections = reader.readtext(work, detail=1, paragraph=False)

    if engine == "trocr":
        if len(languages) != 1 or languages[0] != "en":
            raise ValueError("TrOCR is English-only; use EasyOCR for Hindi or mixed-language input.")
        results = _recognize_lines_trocr(work, _group_chunks(detections),
                                         trocr_model, num_beams, white_bg)
        text = postprocess_text("\n".join(t for _, t, _ in results), spell_correct)
    else:
        results, text = detections, _detections_to_text(detections)
        text = postprocess_text(text, spell_correct)
    return work, results, text


# --------------------------------------------------------------------------
# 5. ★ Public glue-code functions for the lead
# --------------------------------------------------------------------------
def read_handwriting(image_path, languages=("en",), enhance=True, gpu=False,
                    engine="trocr", trocr_model="microsoft/trocr-base-handwritten",
                    num_beams=5, white_bg=True, spell_correct=True) -> str:
    """★ The lead's app.py calls this. Path in → full transcript string out."""
    img = load_image(image_path)
    return analyze(img, languages, enhance, gpu,
                   engine=engine, trocr_model=trocr_model,
                   num_beams=num_beams, white_bg=white_bg,
                   spell_correct=spell_correct)[2]


def read_handwriting_bytes(raw_bytes, languages=("en",), enhance=True, gpu=False,
                          engine="trocr", trocr_model="microsoft/trocr-base-handwritten",
                          num_beams=5, white_bg=True, spell_correct=True) -> str:
    """★ Same, but takes raw file bytes (Streamlit upload / API)."""
    img = load_image_from_bytes(raw_bytes)
    return analyze(img, languages, enhance, gpu,
                   engine=engine, trocr_model=trocr_model,
                   num_beams=num_beams, white_bg=white_bg,
                   spell_correct=spell_correct)[2]


def read_handwriting_detailed(raw_bytes, languages=("en",), enhance=True, gpu=False,
                            engine="trocr", trocr_model="microsoft/trocr-base-handwritten",
                            num_beams=5, white_bg=True, spell_correct=True):
    """Returns (transcript, [(bbox, text, conf), ...]) — used by the UI."""
    img = load_image_from_bytes(raw_bytes)
    _, results, text = analyze(img, languages, enhance, gpu,
                              engine=engine, trocr_model=trocr_model,
                              num_beams=num_beams, white_bg=white_bg,
                              spell_correct=spell_correct)
    return text, results


# --------------------------------------------------------------------------
# 6. Text-to-speech (gTTS — needs internet; browser voice is the backup)
# --------------------------------------------------------------------------
def text_to_speech_bytes(text: str, lang: str = "en") -> bytes:
    """★ Convert transcript → spoken audio (mp3 bytes)."""
    from gtts import gTTS
    if not text.strip():
        raise ValueError("Nothing to speak.")
    buf = io.BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(buf)
    buf.seek(0)
    return buf.getvalue()


# --------------------------------------------------------------------------
# 7. Evaluation metrics (Weeks 9–10 deliverable)
# --------------------------------------------------------------------------
def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate — lower is better."""
    ref = " ".join(reference.split())
    hyp = " ".join(hypothesis.split())
    if not ref:
        return 0.0 if not hyp else 1.0
    return _levenshtein(ref, hyp) / len(ref)


def wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate — lower is better."""
    r, h = reference.split(), hypothesis.split()
    if not r:
        return 0.0 if not h else 1.0
    return _levenshtein(r, h) / len(r)