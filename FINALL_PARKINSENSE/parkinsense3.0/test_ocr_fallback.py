import numpy as np

from handwriting import analyze_with_validation


def _box():
    return [[0, 0], [50, 0], [50, 20], [0, 20]]


def test_analyze_with_validation_retries_when_trocr_text_is_short(monkeypatch):
    def fake_analyze(img_bgr, languages=("en",), enhance=True, gpu=False,
                     engine="trocr", trocr_model=None, num_beams=5,
                     white_bg=True, spell_correct=True):
        if engine == "trocr":
            return img_bgr, [(_box(), "hi", 0.41)], "hi"
        return img_bgr, [(_box(), "hello world from handwriting", 0.9)], "hello world from handwriting"

    monkeypatch.setattr("handwriting.analyze", fake_analyze)

    work, results, text, source, conf = analyze_with_validation(
        np.zeros((64, 64, 3), dtype=np.uint8),
        validator="easyocr",
        min_confidence=0.72,
    )

    assert source == "easyocr"
    assert "hello world" in text
    assert conf >= 0.0
    assert len(results) >= 1
