"""
Fix legacy absolute paths in CSV manifests to match the current workspace directory.
"""
import os
import sys

# Ensure UTF-8 output on Windows
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_AUDIO_DIR = os.path.join(CURRENT_DIR, "output", "processed_audio")
MANIFEST_DIR = os.path.join(CURRENT_DIR, "output", "manifests")

OLD_PREFIX_1 = r"c:\Users\Heli P Shah\OneDrive\Desktop\DEMOOOO\output\processed_audio"
OLD_PREFIX_2 = r"c:/Users/Heli P Shah/OneDrive/Desktop/DEMOOOO/output/processed_audio"

def fix_manifest(filename):
    path = os.path.join(MANIFEST_DIR, filename)
    if not os.path.exists(path):
        print(f"[-] Manifest not found: {path}")
        return
    
    print(f"[*] Checking {filename}...")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    count1 = content.count(OLD_PREFIX_1)
    count2 = content.count(OLD_PREFIX_2)
    total = count1 + count2

    if total > 0:
        content = content.replace(OLD_PREFIX_1, PROCESSED_AUDIO_DIR)
        content = content.replace(OLD_PREFIX_2, PROCESSED_AUDIO_DIR)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] Successfully updated {filename}: fixed {total} paths to:\n    {PROCESSED_AUDIO_DIR}")
    else:
        print(f"[OK] {filename} is already up to date.")

if __name__ == "__main__":
    print(f"Fixing manifest paths in: {MANIFEST_DIR}")
    for fname in ["split_manifest.csv", "cleaned_manifest.csv", "raw_manifest.csv"]:
        fix_manifest(fname)
    print("\n[OK] All manifests verified!")
