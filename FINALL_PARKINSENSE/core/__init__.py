"""
ParkinSense 2.0 Core Package
Unified screening, assistive communication, and clinical progress tracking.
"""

from .spiral import detect_spiral_drawing, analyze_drawing_metrics
from .speech import detect_speech_parkinsons, extract_acoustic_features, transcribe_audio
from .handwriting import read_handwriting, read_handwriting_bytes, analyze_with_validation
from .database import (
    init_db,
    save_activity,
    get_activities,
    delete_activity,
    get_progress_trends,
    get_patient_profile,
    get_reminders,
    toggle_reminder,
)
from .tts import text_to_speech_bytes

__all__ = [
    "detect_spiral_drawing",
    "analyze_drawing_metrics",
    "detect_speech_parkinsons",
    "extract_acoustic_features",
    "transcribe_audio",
    "read_handwriting",
    "read_handwriting_bytes",
    "analyze_with_validation",
    "init_db",
    "save_activity",
    "get_activities",
    "delete_activity",
    "get_progress_trends",
    "get_patient_profile",
    "get_reminders",
    "toggle_reminder",
    "text_to_speech_bytes",
]
