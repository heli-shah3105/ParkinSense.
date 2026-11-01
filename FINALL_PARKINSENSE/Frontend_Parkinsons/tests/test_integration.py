"""
tests/test_integration.py — Complete System Integration Test Suite
==================================================================
Tests all integrated components:
1. SQLite Database & Session persistence
2. PyTorch Deep CNN Spiral Screening (test_image_healthy vs test_image_parkinson)
3. Librosa Voice Acoustic Dysphonia Biomarkers
4. Handwriting OCR & Metric computation (CER / WER)
5. FastAPI REST API endpoints
"""

import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pytest
from starlette.testclient import TestClient

import core
from app import app
SAMPLE_DIR = BASE_DIR / "sample_data"


def test_database_persistence():
    """Verify SQLite database CRUD operations."""
    core.init_db()
    act = core.save_activity(
        activity_type="motor",
        title="Automated Test Spiral",
        snippet="Integration test sample",
        result_label="Healthy",
        confidence=0.95,
        metrics={"smoothness": "85%", "tremor": "None"}
    )
    assert act["id"].startswith("act-")
    assert act["type"] == "motor"

    activities = core.get_activities(limit=10)
    found = any(a["id"] == act["id"] for a in activities)
    assert found is True

    # Delete test entry
    deleted = core.delete_activity(act["id"])
    assert deleted is True


def test_spiral_cnn_model_healthy():
    """Verify CNN screening on healthy benchmark drawing."""
    healthy_path = SAMPLE_DIR / "test_image_healthy.png"
    assert healthy_path.exists(), "Sample test_image_healthy.png missing"

    label, conf, metrics = core.detect_spiral_drawing(healthy_path)
    assert label == "Healthy"
    assert conf >= 0.85
    assert "smoothness" in metrics
    assert "tremor" in metrics


def test_spiral_cnn_model_parkinson():
    """Verify CNN screening on Parkinson benchmark drawing."""
    pd_path = SAMPLE_DIR / "test_image_parkinson.png"
    assert pd_path.exists(), "Sample test_image_parkinson.png missing"

    label, conf, metrics = core.detect_spiral_drawing(pd_path)
    assert label == "Parkinson"
    assert conf >= 0.90
    assert "smoothness" in metrics
    assert "tremor" in metrics


def test_voice_biomarkers():
    """Verify voice acoustic feature extraction & classifier."""
    # Synthesize small test wave
    import numpy as np
    sr = 22050
    t = np.linspace(0, 1.0, sr, False)
    # 150 Hz pure tone
    wave = 0.5 * np.sin(2 * np.pi * 150 * t).astype(np.float32)

    metrics = core.extract_acoustic_features(wave, sr)
    assert "mean_f0_hz" in metrics
    assert "jitter_pct" in metrics
    assert "hnr_db" in metrics

    label, conf, res_metrics = core.detect_speech_parkinsons(wave.tobytes())
    assert label in ["Healthy", "Parkinson"]
    assert 0.0 <= conf <= 1.0


def test_handwriting_metrics():
    """Verify Levenshtein Character Error Rate (CER) & Word Error Rate (WER)."""
    ref = "Take evening medication at 8:00 PM"
    hyp = "Take evening medication at 8:00 PM"
    assert core.handwriting.cer(ref, hyp) == 0.0
    assert core.handwriting.wer(ref, hyp) == 0.0

    hyp_err = "Take evening medcation at 8:00 PM"
    assert core.handwriting.cer(ref, hyp_err) > 0.0


def test_fastapi_endpoints():
    """Verify FastAPI REST API endpoints."""
    client = TestClient(app)

    # Health
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # Profile
    r = client.get("/api/profile")
    assert r.status_code == 200
    assert r.json()["success"] is True

    # History
    r = client.get("/api/history")
    assert r.status_code == 200
    assert "activities" in r.json()

    # Progress
    r = client.get("/api/progress")
    assert r.status_code == 200
    assert "trends" in r.json()

    # Spiral screening via API
    healthy_path = SAMPLE_DIR / "test_image_healthy.png"
    with open(healthy_path, "rb") as f:
        r = client.post("/api/screen/spiral", files={"file": ("test.png", f, "image/png")})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["label"] == "Healthy"
