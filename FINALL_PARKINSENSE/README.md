# ParkinSense 2.0 🧠
### Unified Screening, Assistive Communication, and Longitudinal Progress-Tracking Platform for Parkinson's Patients

> **Important Notice:** ParkinSense 2.0 provides research-grade clinical decision support and screening assistance. It is designed to assist patients, families, and clinicians—not to provide an unassisted standalone medical diagnosis.

---

## 🌟 Overview & Key Components

ParkinSense 2.0 brings together three core functional pillars into a unified architecture:

1. **Screen (Biomarker Detection)**:
   - **Motor Spiral & Wave Assessment**: Deep Convolutional Neural Network (PyTorch / Keras) classifying Archimedean spiral and wave drawings (`Healthy` vs `Parkinson's Disease Indicator`) with confidence scoring, trajectory smoothness, micro-tremor amplitude, and line consistency.
   - **Speech Dysphonia Biomarkers**: Acoustic feature extraction using `librosa` and `scipy` measuring Fundamental Frequency ($F_0$), Jitter % (cycle-to-cycle frequency variation), Shimmer % (amplitude perturbation), and Harmonics-to-Noise Ratio (HNR in dB).

2. **Communicate (Assistive Interaction)**:
   - **Handwriting Digitization & OCR**: Enhances shaky and micrographic handwriting using morphological pre-processing (bilateral/fastNlMeans denoising, CLAHE contrast flattening), followed by Microsoft TrOCR / EasyOCR line recognition, dictionary spelling correction, and Character Error Rate (CER) calculation.
   - **Speech-to-Text & Text-to-Speech**: Speech transcription coupled with multi-lingual audio readback (English, Hindi, Marathi, Spanish, French, German) using `gTTS` and offline browser `speechSynthesis`.

3. **Track (Longitudinal Clinical Analytics)**:
   - **Persistent SQLite Storage**: Zero-configuration local database (`data/parkinsense.db`) logging every session, date, score, acoustic metrics, drawing variance, and transcription.
   - **Interactive Progress Curves**: Real-time trend visualizers tracking recovery, medication response, and motor consistency over time.
   - **Caregiver & Doctor Portal**: Multi-patient roster with risk stratification, status badges, and one-click printable clinical summary reports.

---

## 🏗️ Project Architecture

```
FINALL_PARKINSENSE/
├── app.py                     # FastAPI application serving Web Frontend & all REST APIs
├── app_streamlit.py           # Streamlit companion app matching project plan
├── run.py                     # Unified one-click application launcher
├── requirements.txt           # Unified dependency specifications
├── models/
│   ├── spiral_model.pt        # Trained PyTorch CNN weights (converted from parkinson_disease_detection.h5)
│   └── parkinson_disease_detection.h5 # Original HDF5 model
├── core/
│   ├── __init__.py            # Clean unified exports
│   ├── spiral.py              # CNN classifier & Archimedean trajectory biomechanics
│   ├── speech.py              # Acoustic dysphonia analysis (Jitter, Shimmer, HNR, F0)
│   ├── handwriting.py         # Advanced OCR pipeline (EasyOCR / TrOCR / Gemini / SpellCheck)
│   ├── handwriting_cloud.py   # Gemini Cloud transcription fallback
│   ├── database.py            # SQLite session storage, reminders, profile, progress trends
│   └── tts.py                 # Multi-lingual text-to-speech engine
├── frontend/                  # Full-Stack Web Application
│   ├── index.html             # Entry redirect
│   ├── landing_page/          # Cursive "hello" and audio waveform intro animation
│   │   ├── index.html
│   │   ├── style.css
│   │   └── script.js
│   └── dashboard/             # Complete Assistive Care Suite Dashboard
│       ├── index.html
│       ├── style.css
│       └── app.js             # Live REST API client with offline fallback
├── sample_data/               # Preloaded dataset validation samples
│   ├── test_image_healthy.png # Benchmark healthy spiral drawing
│   └── test_image_parkinson.png # Benchmark Parkinson spiral drawing
├── data/
│   └── parkinsense.db         # Persistent SQLite database (auto-generated)
└── tests/
    └── test_integration.py    # Pytest integration test suite
```

---

## 🚀 Quickstart & How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application

#### Option A: Full-Stack Web Application (Recommended)
```bash
python run.py
```
* Automatically starts the FastAPI server and launches your default browser at `http://localhost:8000`.
* Experience the animated **Waveform & Cursive Hello Landing Page** and click **"ENTER DASHBOARD"** to access the complete Assistive Care Suite!

#### Option B: Streamlit Companion App
```bash
python run.py --streamlit
# or: streamlit run app_streamlit.py
```
* Launches the multi-page Streamlit application on `http://localhost:8501` featuring multi-language switcher (English / Hindi / Marathi), line charts, and interactive tests.

#### Option C: Run Both Simultaneously
```bash
python run.py --all
```

---

## 🔬 Testing the AI Models

You can immediately test the integrated models using the included test data:

1. **Spiral Motor Test**:
   - Navigate to the **Spiral (Parkinson's Detection)** tab in the dashboard.
   - Click **"Sample (Healthy)"** to see the CNN predict **Healthy (93.7% confidence)** with mild tremor and 82% smoothness.
   - Click **"Sample (Parkinson)"** to see the CNN predict **Parkinson's Indicator (99.6% confidence)** with elevated trajectory variance and moderate tremor.
   - You can also draw freely on the Archimedean canvas or upload any custom drawing.

2. **Speech Test**:
   - Tap the microphone in the **Speak** tab to record your voice.
   - The system extracts pitch stability ($F_0$), cycle-to-cycle frequency Jitter %, cycle-to-cycle amplitude Shimmer %, and HNR ratio.
   - Transcribe and click **"Listen (Voice)"** or **"Translate"** to hear spoken translations in Hindi or Marathi.

3. **Handwriting OCR**:
   - In the **Write** tab, draw on screen or click **"Upload Note Image"** / **"Medicine Note Sample"**.
   - Watch the OCR engine convert handwritten notes to searchable digital text with one-click voice read aloud.

---

## 🧪 Running Automated Tests

Run the test suite to verify all modules and REST API endpoints:
```bash
pytest tests/test_integration.py -v
```

---

## 🛡️ Clinical Disclaimer
This software is intended for research, assistive accessibility, and decision-support purposes. It is not approved as a medical device or diagnostic instrument. Any concerning motor or speech symptoms should be evaluated by a qualified neurologist or movement disorders specialist.
