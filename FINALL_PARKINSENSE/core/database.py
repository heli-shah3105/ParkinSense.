"""
core/database.py — SQLite Storage Layer for ParkinSense 2.0
===========================================================
Persistent local storage for:
- Patient Sessions & Activity Log (Speech, Handwriting, Motor Spiral tests)
- Screening scores and quantitative metrics over time
- Reminders and daily patient tasks
- Doctor / Caregiver patient profile and rosters
"""

import os
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "parkinsense.db"


def get_db_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite schema and populates default baseline profile & activity seeds."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS activities (
        id TEXT PRIMARY KEY,
        activity_type TEXT NOT NULL,  -- 'speech', 'writing', 'motor'
        title TEXT NOT NULL,
        snippet TEXT NOT NULL,
        result_label TEXT,           -- 'Healthy', 'Parkinson', 'Completed', etc.
        confidence REAL,             -- 0.0 to 1.0
        metrics TEXT,                -- JSON string of metrics dictionary
        date_str TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        full_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Completed',
        translation TEXT,
        target_lang TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0,
        time_hint TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_profile (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        dob TEXT,
        age INTEGER,
        joined_date TEXT,
        doctor TEXT,
        contact TEXT,
        emergency TEXT,
        speech_count INTEGER DEFAULT 0,
        writing_count INTEGER DEFAULT 0,
        motor_count INTEGER DEFAULT 0
    );
    """)

    # Check if patient exists, if not seed default
    cur.execute("SELECT COUNT(*) FROM patient_profile")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO patient_profile (id, name, dob, age, joined_date, doctor, contact, emergency, speech_count, writing_count, motor_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "PV-88942",
            "Eleanor Vance",
            "August 14, 1968",
            58,
            "January 12, 2026",
            "Dr. Robert Sterling, MD",
            "+1 (555) 382-9912",
            "Arthur Vance (Spouse) - +1 (555) 882-1049",
            24, 18, 7
        ))

    # Check if reminders exist, if not seed
    cur.execute("SELECT COUNT(*) FROM reminders")
    if cur.fetchone()[0] == 0:
        default_reminders = [
            ("Morning Speech Practice Exercise", 1, "9:00 AM"),
            ("Handwriting Digitization Task", 1, "11:30 AM"),
            ("Evening Motor Assessment (Spiral)", 0, "7:00 PM")
        ]
        cur.executemany("INSERT INTO reminders (text, completed, time_hint) VALUES (?, ?, ?)", default_reminders)

    # Check if activities exist, if not seed baseline
    cur.execute("SELECT COUNT(*) FROM activities")
    if cur.fetchone()[0] == 0:
        default_activities = [
            (
                "act-101",
                "speech",
                "Speech → Text Transcription",
                "I would like to visit the doctor tomorrow morning.",
                "Normal Pitch",
                0.91,
                json.dumps({"words": 42, "audio_sec": 12, "hnr_db": 19.4, "jitter_pct": 0.42}),
                "Today, 10:42 AM",
                "Sep 25, 2026",
                "Completed",
                "मुझे कल सुबह डॉक्टर के पास जाना है।",
                "Hindi"
            ),
            (
                "act-102",
                "writing",
                "Handwriting → Text OCR",
                "Take evening medicine at 8:00 PM precisely.",
                "Recognized",
                0.94,
                json.dumps({"words": 28, "clarity": "High", "engine": "TrOCR"}),
                "Today, 09:15 AM",
                "Sep 25, 2026",
                "Completed",
                "8.00 PM ला संध्याकाळचे औषध घ्या.",
                "Marathi"
            ),
            (
                "act-103",
                "motor",
                "Spiral Motor Assessment",
                "Archimedean spiral drawing screening completed.",
                "Healthy",
                0.93,
                json.dumps({"tremor": "Mild", "smoothness": "84%", "deviation": "Low", "consistency": "81%", "model_conf": 93.7}),
                "Yesterday, 06:30 PM",
                "Sep 24, 2026",
                "Completed",
                None,
                None
            ),
            (
                "act-104",
                "speech",
                "Speech Acoustic Screening",
                "Sustained vowel phonation test /a/.",
                "Healthy",
                0.88,
                json.dumps({"jitter_pct": 0.48, "shimmer_pct": 2.1, "hnr_db": 18.2, "f0_hz": 174.5}),
                "Sep 23, 2026",
                "Sep 23, 2026",
                "Completed",
                None,
                None
            ),
            (
                "act-105",
                "motor",
                "Spiral Motor Assessment",
                "Baseline motor assessment session.",
                "Healthy",
                0.89,
                json.dumps({"tremor": "Mild", "smoothness": "78%", "deviation": "Low", "consistency": "79%"}),
                "Sep 21, 2026",
                "Sep 21, 2026",
                "Completed",
                None,
                None
            )
        ]
        cur.executemany("""
        INSERT INTO activities (id, activity_type, title, snippet, result_label, confidence, metrics, date_str, full_date, status, translation, target_lang)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, default_activities)

    conn.commit()
    conn.close()


def save_activity(
    activity_type: str,
    title: str,
    snippet: str,
    result_label: Optional[str] = None,
    confidence: Optional[float] = None,
    metrics: Optional[Dict[str, Any]] = None,
    translation: Optional[str] = None,
    target_lang: Optional[str] = None,
    status: str = "Completed"
) -> Dict[str, Any]:
    """Persists a new patient session record into the SQLite database."""
    conn = get_db_connection()
    cur = conn.cursor()

    act_id = f"act-{int(datetime.now().timestamp() * 1000)}"
    now = datetime.now()
    date_str = f"Today, {now.strftime('%I:%M %p')}"
    full_date = now.strftime("%b %d, %Y")
    metrics_str = json.dumps(metrics or {})

    cur.execute("""
    INSERT INTO activities (id, activity_type, title, snippet, result_label, confidence, metrics, date_str, full_date, status, translation, target_lang)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (act_id, activity_type, title, snippet, result_label, confidence, metrics_str, date_str, full_date, status, translation, target_lang))

    # Update counts in patient_profile
    if activity_type == "speech":
        cur.execute("UPDATE patient_profile SET speech_count = speech_count + 1 WHERE id = 'PV-88942'")
    elif activity_type == "writing":
        cur.execute("UPDATE patient_profile SET writing_count = writing_count + 1 WHERE id = 'PV-88942'")
    elif activity_type == "motor":
        cur.execute("UPDATE patient_profile SET motor_count = motor_count + 1 WHERE id = 'PV-88942'")

    conn.commit()
    conn.close()

    return {
        "id": act_id,
        "type": activity_type,
        "title": title,
        "snippet": snippet,
        "result_label": result_label,
        "confidence": confidence,
        "metrics": metrics or {},
        "date": date_str,
        "fullDate": full_date,
        "status": status,
        "translation": translation,
        "targetLang": target_lang
    }


def get_activities(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches logged sessions sorted latest first."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activities ORDER BY timestamp DESC, id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()

    results = []
    for r in rows:
        metrics_dict = {}
        try:
            metrics_dict = json.loads(r["metrics"]) if r["metrics"] else {}
        except Exception:
            metrics_dict = {}

        metrics_summary = ""
        if r["activity_type"] == "speech":
            metrics_summary = f"{metrics_dict.get('words', len(r['snippet'].split()))} words"
        elif r["activity_type"] == "writing":
            metrics_summary = f"{metrics_dict.get('words', len(r['snippet'].split()))} words recognized"
        elif r["activity_type"] == "motor":
            c = metrics_dict.get('consistency', '80%')
            s = metrics_dict.get('smoothness', '75%')
            t = metrics_dict.get('tremor', 'Mild')
            metrics_summary = f"Consistency: {c} • Smoothness: {s} • Tremor: {t}"

        results.append({
            "id": r["id"],
            "type": r["activity_type"],
            "title": r["title"],
            "snippet": r["snippet"],
            "result_label": r["result_label"],
            "confidence": r["confidence"],
            "metrics": metrics_summary,
            "metrics_data": metrics_dict,
            "date": r["date_str"],
            "fullDate": r["full_date"],
            "status": r["status"],
            "translation": r["translation"],
            "targetLang": r["target_lang"]
        })
    return results


def delete_activity(act_id: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM activities WHERE id = ?", (act_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_patient_profile() -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patient_profile LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if not row:
        return {}
    return dict(row)


def get_reminders() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reminders ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r["id"], "text": r["text"], "completed": bool(r["completed"]), "time": r["time_hint"]} for r in rows]


def toggle_reminder(reminder_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE reminders SET completed = CASE WHEN completed = 1 THEN 0 ELSE 1 END WHERE id = ?", (reminder_id,))
    updated = cur.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def get_progress_trends() -> Dict[str, Any]:
    """Computes robust, aligned longitudinal progress trends for both web and Streamlit dashboards."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, activity_type, title, result_label, confidence, metrics, full_date, date_str, timestamp FROM activities ORDER BY timestamp ASC, id ASC")
    rows = cur.fetchall()
    conn.close()

    sessions = []
    motor_timeline = []
    speech_timeline = []
    writing_timeline = []

    latest_motor = 80.0
    latest_speech = 85.0
    latest_writing = 82.0

    aligned_sessions = []

    for idx, r in enumerate(rows, 1):
        m = {}
        try:
            m = json.loads(r["metrics"]) if r["metrics"] else {}
        except Exception:
            m = {}

        act_type = r["activity_type"]
        date_label = r["full_date"] or r["date_str"] or f"Session {idx}"

        if act_type == "motor":
            score = 80.0
            if "smoothness" in m:
                score = float(str(m["smoothness"]).replace("%", ""))
            elif r["confidence"]:
                score = round(r["confidence"] * 100, 1)
            latest_motor = score
            motor_timeline.append({
                "session": f"S{len(motor_timeline) + 1}",
                "date": date_label,
                "score": score,
                "tremor": m.get("tremor", "Mild"),
                "consistency": m.get("consistency", "80%"),
                "label": r["result_label"] or "Healthy"
            })
        elif act_type == "speech":
            score = round((r["confidence"] or 0.85) * 100, 1)
            latest_speech = score
            speech_timeline.append({
                "session": f"S{len(speech_timeline) + 1}",
                "date": date_label,
                "score": score,
                "jitter": m.get("jitter_pct", 0.42),
                "shimmer": m.get("shimmer_pct", 2.1),
                "hnr": m.get("hnr_db", 19.4),
                "label": r["result_label"] or "Normal"
            })
        elif act_type == "writing":
            score = round((r["confidence"] or 0.82) * 100, 1)
            latest_writing = score
            writing_timeline.append({
                "session": f"S{len(writing_timeline) + 1}",
                "date": date_label,
                "score": score,
                "engine": m.get("engine", "TrOCR"),
                "words": m.get("words", 20)
            })

        aligned_sessions.append({
            "session": f"Session {idx}",
            "date": date_label,
            "type": act_type,
            "motorScore": latest_motor,
            "speechScore": latest_speech,
            "writingScore": latest_writing
        })

    if not aligned_sessions:
        dates = ["Sep 20", "Sep 21", "Sep 22", "Sep 23", "Sep 24", "Sep 25", "Today"]
        m_vals = [72, 74, 76, 75, 78, 81, 84]
        s_vals = [70, 73, 75, 76, 79, 82, 85]
        w_vals = [68, 71, 74, 76, 77, 80, 82]
        aligned_sessions = [
            {"session": f"Session {i+1}", "date": dates[i], "type": "baseline", "motorScore": m_vals[i], "speechScore": s_vals[i], "writingScore": w_vals[i]}
            for i in range(len(dates))
        ]

    labels = [s["date"] for s in aligned_sessions]
    motor_scores = [s["motorScore"] for s in aligned_sessions]
    speech_scores = [s["speechScore"] for s in aligned_sessions]
    writing_scores = [s["writingScore"] for s in aligned_sessions]

    avg_motor = round(sum(motor_scores) / len(motor_scores), 1) if motor_scores else 80.0
    avg_speech = round(sum(speech_scores) / len(speech_scores), 1) if speech_scores else 85.0
    
    return {
        "labels": labels[-10:],
        "motorScores": motor_scores[-10:],
        "speechScores": speech_scores[-10:],
        "writingScores": writing_scores[-10:],
        "alignedSessions": aligned_sessions[-15:],
        "motorTimeline": motor_timeline,
        "speechTimeline": speech_timeline,
        "writingTimeline": writing_timeline,
        "latestMotorSmoothness": motor_scores[-1] if motor_scores else 81,
        "latestSpeechClarity": speech_scores[-1] if speech_scores else 85,
        "avgMotorSmoothness": avg_motor,
        "avgSpeechClarity": avg_speech,
        "totalSessions": len(aligned_sessions)
    }
