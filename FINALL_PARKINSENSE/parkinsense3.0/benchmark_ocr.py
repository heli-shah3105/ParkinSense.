"""Benchmark OCR engines on the sample handwriting pages in test_images/.

Usage:
    python benchmark_ocr.py
    python benchmark_ocr.py --engines easyocr trocr gemini
    python benchmark_ocr.py --api-key YOUR_KEY
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from handwriting import cer, read_handwriting
from handwriting_cloud import read_handwriting_bytes

IMG_DIR = Path("test_images")
GT_DIR = Path("ground_truth")
DEFAULT_TROCR_MODEL = "microsoft/trocr-base-handwritten"


def load_truth(img_path: Path) -> str:
    gt_path = GT_DIR / (img_path.stem + ".txt")
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth missing for {img_path.name}: {gt_path}")
    return gt_path.read_text(encoding="utf-8")


def get_image_files():
    if not IMG_DIR.exists():
        return []
    return sorted(
        p for p in IMG_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    )


def predict_easyocr(img_path: Path) -> str:
    return read_handwriting(
        str(img_path),
        languages=("en",),
        enhance=True,
        engine="easyocr",
        trocr_model=DEFAULT_TROCR_MODEL,
        num_beams=5,
        white_bg=True,
        spell_correct=True,
    )


def predict_trocr(img_path: Path, trocr_model: str = DEFAULT_TROCR_MODEL) -> str:
    return read_handwriting(
        str(img_path),
        languages=("en",),
        enhance=True,
        engine="trocr",
        trocr_model=trocr_model,
        num_beams=5,
        white_bg=True,
        spell_correct=True,
    )


def predict_gemini(img_path: Path, api_key: str | None = None) -> str:
    raw = img_path.read_bytes()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }.get(img_path.suffix.lower(), "image/jpeg")
    return read_handwriting_bytes(raw, mime=mime, api_key=api_key or os.getenv("GEMINI_API_KEY"))


def benchmark_one(engine: str, images, api_key: str | None = None, trocr_model: str = DEFAULT_TROCR_MODEL):
    scores = []
    errors = []

    for img_path in images:
        try:
            truth = load_truth(img_path)
            if engine == "easyocr":
                prediction = predict_easyocr(img_path)
            elif engine == "trocr":
                prediction = predict_trocr(img_path, trocr_model=trocr_model)
            elif engine == "gemini":
                prediction = predict_gemini(img_path, api_key=api_key)
            else:
                raise ValueError(f"Unknown engine: {engine}")
            score = cer(truth, prediction)
            scores.append(score)
            print(f"{engine:<8} {img_path.name:<18} CER={score:>7.1%}  pred={prediction[:40]!r}")
        except Exception as exc:  # keep benchmark going even if one image fails
            errors.append((img_path.name, str(exc)))
            print(f"{engine:<8} {img_path.name:<18} ERROR: {exc}")

    avg = sum(scores) / len(scores) if scores else 0.0
    print(f"{engine:<8} AVERAGE CER = {avg:>7.1%}")
    if errors:
        print(f"{engine:<8} ERRORS = {len(errors)}")
    print("-" * 90)
    return avg


def main():
    parser = argparse.ArgumentParser(description="Benchmark EasyOCR, TrOCR, and Gemini on handwriting samples.")
    parser.add_argument("--engines", nargs="+", default=["easyocr", "trocr", "gemini"],
                        choices=["easyocr", "trocr", "gemini"])
    parser.add_argument("--api-key", default=None, help="Gemini API key. Optional if GEMINI_API_KEY is set.")
    parser.add_argument("--trocr-model", default=DEFAULT_TROCR_MODEL,
                        help="TrOCR model name, e.g. microsoft/trocr-base-handwritten")
    args = parser.parse_args()

    images = get_image_files()
    if not images:
        print(f"No sample images found in {IMG_DIR}/. Add photos to compare OCR engines.")
        return 0

    missing_gt = []
    valid_images = []
    for img in images:
        if not (GT_DIR / (img.stem + ".txt")).exists():
            missing_gt.append(img.name)
        else:
            valid_images.append(img)

    if not valid_images:
        print(f"No ground-truth labels found in {GT_DIR}/. Add *.txt files matching your test images.")
        return 0

    if missing_gt:
        print(f"Skipping {len(missing_gt)} image(s) without ground truth: {', '.join(missing_gt[:10])}")

    print("ParkinSense OCR benchmark")
    print(f"Images: {len(valid_images)}")
    print(f"Engines: {', '.join(args.engines)}")
    print(f"TrOCR model: {args.trocr_model}")
    print("-" * 90)

    results = {}
    for engine in args.engines:
        results[engine] = benchmark_one(engine, valid_images, api_key=args.api_key, trocr_model=args.trocr_model)

    print("SUMMARY")
    for engine, score in results.items():
        print(f"{engine:<8} avg CER = {score:>7.1%}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
