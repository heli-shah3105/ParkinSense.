"""
Put 20–30 handwriting photos in  test_images/
and the true sentence for each in ground_truth/<same-name>.txt
Then:  python evaluate_cer.py
"""
import sys
from pathlib import Path
from handwriting import read_handwriting, cer

IMG_DIR = Path("test_images")
GT_DIR = Path("ground_truth")
LANGS = ("en",)   # ("hi", "en") for Hindi pages

def main():
    images = sorted(p for p in IMG_DIR.iterdir()
                    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"})
    if not images:
        sys.exit(f"No images found in {IMG_DIR}/ — add your 20–30 test photos first.")

    scores = []
    print(f"{'image':<18}{'CER':>8}   transcript preview")
    print("-" * 70)
    for img_path in images:
        gt_path = GT_DIR / (img_path.stem + ".txt")
        if not gt_path.exists():
            print(f"{img_path.name:<18}{'—':>8}   (no ground_truth file, skipped)")
            continue
        truth = gt_path.read_text(encoding="utf-8")
        pred = read_handwriting(str(img_path), languages=LANGS)
        score = cer(truth, pred)
        scores.append(score)
        print(f"{img_path.name:<18}{score:>7.1%}   {pred[:45]!r}")

    if scores:
        print("-" * 70)
        print(f"Average Character Error Rate: {sum(scores)/len(scores):.1%} over {len(scores)} pages")

if __name__ == "__main__":
    main()