"""
=============================================================================
VocalAid AI — Complete System & Pipeline Verification Test Suite
=============================================================================
Runs end-to-end diagnostic checks:
  1. Python & ML Environment (PyTorch, CUDA, Transformers, PEFT, SoundFile)
  2. Configuration & Workspace Directory Resolution
  3. Preprocessed Datasets & Audio Manifest Alignment
  4. Trained LoRA Adapters (Generalized & Personalized)
  5. Live Model Inference & Transcription Test with Word Timestamps
=============================================================================
"""

import os
import sys
import time

# Ensure UTF-8 output and line buffering on Windows
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def p(msg=""):
    print(msg, flush=True)

p("\n" + "=" * 70)
p("VOCALAID AI — SYSTEM VERIFICATION & PIPELINE TEST")
p("=" * 70)

passed_tests = 0
total_tests = 5

# ── TEST 1: Python & ML Libraries ───────────────────────────────────────────
p("\n[TEST 1/5] Checking Python & Machine Learning Dependencies...")
try:
    import torch
    import soundfile as sf
    import numpy as np
    import transformers
    import peft
    import librosa

    cuda_avail = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU Only"

    p(f"  [OK] Python:       {sys.version.split()[0]} ({sys.executable})")
    p(f"  [OK] PyTorch:      {torch.__version__} (CUDA: {cuda_avail} - {device_name})")
    p(f"  [OK] Transformers: {transformers.__version__}")
    p(f"  [OK] PEFT:         {peft.__version__}")
    p(f"  [OK] SoundFile:    {sf.__version__}")
    p(f"  [OK] Librosa:      {librosa.__version__}")
    p("  --> TEST 1 PASSED: All core ML modules are installed and operational.")
    passed_tests += 1
except Exception as e:
    p(f"  [FAIL] Dependency error: {e}")
    p("  --> Please run with conda environment: conda activate dysarthric")

# ── TEST 2: Workspace Paths & Config ────────────────────────────────────────
p("\n[TEST 2/5] Checking Workspace Directory Structure & Configuration...")
try:
    from config import (
        BASE_DIR, OUTPUT_DIR, PROCESSED_AUDIO_DIR, MANIFEST_DIR,
        ADAPTER_DIR, LOGS_DIR, resolve_audio_path
    )

    p(f"  [OK] BASE_DIR:            {BASE_DIR}")
    p(f"  [OK] PROCESSED_AUDIO_DIR: {PROCESSED_AUDIO_DIR} (Exists: {os.path.exists(PROCESSED_AUDIO_DIR)})")
    p(f"  [OK] MANIFEST_DIR:        {MANIFEST_DIR} (Exists: {os.path.exists(MANIFEST_DIR)})")
    p(f"  [OK] ADAPTER_DIR:         {ADAPTER_DIR} (Exists: {os.path.exists(ADAPTER_DIR)})")

    assert os.path.exists(PROCESSED_AUDIO_DIR), "processed_audio directory missing"
    assert os.path.exists(MANIFEST_DIR), "manifests directory missing"
    assert os.path.exists(ADAPTER_DIR), "adapters directory missing"

    p("  --> TEST 2 PASSED: Configuration and workspace paths are valid.")
    passed_tests += 1
except Exception as e:
    p(f"  [FAIL] Path error: {e}")

# ── TEST 3: Manifests & Dataset Alignment ───────────────────────────────────
p("\n[TEST 3/5] Checking Manifests & Preprocessed Audio Files...")
try:
    import pandas as pd

    split_manifest = os.path.join(MANIFEST_DIR, "split_manifest.csv")
    cleaned_manifest = os.path.join(MANIFEST_DIR, "cleaned_manifest.csv")

    assert os.path.exists(split_manifest), f"Missing: {split_manifest}"
    df_split = pd.read_csv(split_manifest)
    p(f"  [OK] split_manifest.csv:   {len(df_split)} samples across {df_split['speaker_id'].nunique()} speakers")

    # Verify audio file resolution
    first_row_audio = resolve_audio_path(str(df_split.iloc[0]["audio_path"]))
    audio_exists = os.path.exists(first_row_audio)
    p(f"  [OK] Sample audio path:   {os.path.basename(first_row_audio)} (Found on disk: {audio_exists})")

    assert audio_exists, f"Audio file not found: {first_row_audio}"

    # Count speakers in processed_audio
    speakers = [d for d in os.listdir(PROCESSED_AUDIO_DIR) if os.path.isdir(os.path.join(PROCESSED_AUDIO_DIR, d))]
    p(f"  [OK] Processed speakers:  {len(speakers)} speaker folders ready in output/processed_audio")

    p("  --> TEST 3 PASSED: Manifests and processed audio files are properly linked.")
    passed_tests += 1
except Exception as e:
    p(f"  [FAIL] Manifest test error: {e}")

# ── TEST 4: LoRA Adapters ───────────────────────────────────────────────────
p("\n[TEST 4/5] Checking Trained LoRA Adapters...")
try:
    from step6_inference import DysarthricSpeechTranscriber

    adapter_info = DysarthricSpeechTranscriber.list_available_adapters()
    gen_avail = adapter_info["generalized_adapter"]["available"]
    spk_count = adapter_info["count_speaker_adapters"]

    p(f"  [OK] Generalized Adapter: {'Available (Trained)' if gen_avail else 'Not Found'}")
    p(f"  [OK] Personal Adapters:   {spk_count} speaker adapters detected")

    for spk, meta in sorted(adapter_info["speaker_adapters"].items())[:5]:
        p(f"       - {spk:10s} [{meta['severity']:8s}] -> {os.path.basename(meta['path'])}")
    if spk_count > 5:
        p(f"       ... and {spk_count - 5} more personalized adapters")

    assert gen_avail, "Generalized adapter not found"
    assert spk_count > 0, "No personalized speaker adapters found"

    p("  --> TEST 4 PASSED: Both generalized and personalized adapters are ready.")
    passed_tests += 1
except Exception as e:
    p(f"  [FAIL] Adapter test error: {e}")

# ── TEST 5: End-to-End Transcription Inference Test ─────────────────────────
p("\n[TEST 5/5] Performing Live End-to-End Transcription Test...")
try:
    # Pick a reliable sample from F3_M03 or UA_CF02
    test_sample = None
    for cand in [
        os.path.join(PROCESSED_AUDIO_DIR, "UA_CF02", "UA_CF02_000000.wav"),
        os.path.join(PROCESSED_AUDIO_DIR, "F3_M03", "F3_M03_002501.wav"),
    ]:
        if os.path.exists(cand):
            test_sample = cand
            break

    if not test_sample:
        # Fallback to any wav
        import glob
        all_wavs = glob.glob(os.path.join(PROCESSED_AUDIO_DIR, "*", "*.wav"))
        if all_wavs:
            test_sample = all_wavs[0]

    assert test_sample and os.path.exists(test_sample), "Could not find any audio sample to test"

    p(f"  [*] Loading ASR Transcriber on: {'cuda' if torch.cuda.is_available() else 'cpu'}...")
    t0 = time.time()
    transcriber = DysarthricSpeechTranscriber()
    t_load = time.time() - t0
    p(f"  [OK] Model loaded in {t_load:.2f}s (Active: {transcriber.current_adapter_name})")

    p(f"  [*] Transcribing test clip: {os.path.basename(test_sample)}...")
    t1 = time.time()
    result = transcriber.transcribe_with_timestamps(test_sample)
    t_infer = time.time() - t1

    p("\n  " + "-" * 50)
    p(f"  Transcription: \"{result['transcription']}\"")
    p(f"  Confidence:    {result['confidence'] * 100:.1f}%")
    p(f"  Duration:      {result['duration_sec']}s")
    p(f"  Latency:       {t_infer:.2f}s")
    p(f"  Adapter Used:  {result['adapter_used']}")
    if result.get("words"):
        p(f"  Word count:    {len(result['words'])} words timestamped")
    p("  " + "-" * 50)

    assert result["transcription"] is not None, "Transcription output was None"
    p("\n  --> TEST 5 PASSED: Live inference transcribed audio successfully!")
    passed_tests += 1
except Exception as e:
    p(f"  [FAIL] Inference test error: {e}")
    import traceback
    traceback.print_exc()

# ── SUMMARY ─────────────────────────────────────────────────────────────────
p("\n" + "=" * 70)
p(f"TEST RESULTS: {passed_tests}/{total_tests} PASSED")
if passed_tests == total_tests:
    p("STATUS: ALL SYSTEMS OPERATIONAL - READY FOR BENCHMARKING & WEB PLATFORM")
else:
    p(f"STATUS: {total_tests - passed_tests} TEST(S) FAILED - Review logs above")
p("=" * 70 + "\n")
