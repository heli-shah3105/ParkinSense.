# ParkinSense 2.0 🧠
### Unified AI-Driven Screening, Assistive Communication, and Longitudinal Progress-Tracking Platform for Parkinson's Disease

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red.svg)](https://pytorch.org/)
[![Wav2Vec2](https://img.shields.io/badge/Acoustic_Model-Wav2Vec2%20%2B%20LoRA-orange.svg)](https://huggingface.co/facebook/wav2vec2-base-960h)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Clinical Notice:** *ParkinSense 2.0 provides clinical decision support and screening assistance for patients, families, and clinicians. It is designed for early biomarker detection and progress tracking.*

---

## 🌟 Architecture & Core Modules

ParkinSense 2.0 combines multimodal clinical AI screening with specialized assistive communication:

```
ParkinSense/
├── FINALL_PARKINSENSE/          # Multimodal Clinical Screening & Patient Dashboard Suite
│   ├── app.py                   # FastAPI REST API & Web Dashboard Server
│   ├── app_streamlit.py         # Streamlit Clinical Companion Application
│   ├── run.py                   # One-Click Unified Launcher
│   ├── requirements.txt         # Core dependencies
│   ├── ParkinSense2.0—FullProjectPlan.pdf # Comprehensive Clinical Architecture Plan
│   ├── core/                    # Screening AI Engines
│   │   ├── spiral.py            # Deep CNN classifier & Archimedean trajectory biomechanics
│   │   ├── speech.py            # Acoustic dysphonia analysis (Jitter, Shimmer, HNR, F0)
│   │   ├── handwriting.py       # Shaky handwriting restoration & TrOCR / EasyOCR pipeline
│   │   ├── database.py          # Persistent SQLite patient database & progress curves
│   │   └── tts.py               # Multilingual Text-to-Speech audio readback
│   └── frontend/                # Interactive Patient & Caregiver UI
│       ├── landing_page/        # Cursive "hello" and audio waveform intro animation
│       └── dashboard/           # Comprehensive Assistive Care Suite Dashboard
│
└── DEMOOOO/                     # VocalAid AI — High-Performance Dysarthric Speech Platform
    ├── app.py                   # Interactive Web Platform (16 kHz Web Audio + Real-Time ASR)
    ├── step6_inference.py       # Wav2Vec2 + LoRA Real-Time Speech Decoder (<1s latency)
    ├── lexicon_decoder.py       # Pure-Python Clinical Lexicon & Dysarthric Phonetic Rescorer
    ├── config.py                # Acoustic configuration & speaker metadata
    ├── step1_build_manifest.py  # Manifest dataset pipeline
    ├── step2_preprocess.py      # Audio standardization & volume normalization
    ├── step3_split_speakers.py  # Clinical speaker train/val/test stratification
    ├── step4_model_setup.py     # LoRA adapter injection for Wav2Vec2
    ├── step5_train.py           # Multi-speaker generalized & personalized training
    ├── benchmark.py             # Accuracy (WER/CER) & clinical pathology benchmark
    └── run_app.bat              # One-click Windows launcher
```

---

## 🔬 Key Capabilities

### 1. Motor Biomarker Screening (Spiral & Wave Drawings)
- **Deep CNN Classification**: Classifies Archimedean spiral and Meander wave drawings (`Healthy` vs `Parkinson's Indicator`).
- **Biomechanical Metrics**: Computes trajectory smoothness, micro-tremor amplitude, and pen-stroke consistency.

### 2. Vocal Dysphonia Analysis
- **Acoustic Profiling**: Extracts Fundamental Frequency ($F_0$), Jitter % (frequency perturbation), Shimmer % (amplitude perturbation), and Harmonics-to-Noise Ratio (HNR in dB) to detect early vocal fold rigidity.

### 3. Assistive Handwriting Digitization
- **Tremor Suppression**: Morphological denoising and contrast adaptive filtering (CLAHE).
- **OCR Engine**: Transcribes micrographic and shaky handwriting into clear digital text using OCR with dictionary correction.

### 4. Real-Time Dysarthric Speech Recognition (VocalAid AI)
- **Acoustic Model**: Meta Wav2Vec2-960h fine-tuned with Low-Rank Adaptation (LoRA rank-16).
- **Dual-Mode Engine**: 
  - *Standard Speech Mode*: Instant (<0.5s) real-time translation for conversational English.
  - *Dysarthric LoRA Mode*: Compensates for severe hypophonia, imprecise consonants, and vowel centralizations.
- **Pure-Python Clinical Decoder**: Phonetic error correction mapping common Parkinsonian distortions (`"cmpter" -> "computer"`, `"bacspas" -> "backspace"`, `"dat" -> "that"`).
- **Speech Pathology Metrics**: Real-time Words-Per-Minute (WPM), pause ratio, and articulation rate.

### 5. Longitudinal Tracking & Caregiver Portal
- **Persistent Storage**: Auto-managed SQLite database (`data/parkinsense.db`).
- **Progress Curves**: Visual trends tracking motor stability and speech clarity over time.

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.10 or 3.11
- Recommended: Conda environment (`conda create -n dysarthric python=3.10`)
- FFmpeg (for audio processing)

### Setup
```bash
git clone https://github.com/heli-shah3105/ParkinSense.git
cd ParkinSense
```

### Running the Applications

#### 1. Launch the Multimodal Screening Suite:
```bash
cd FINALL_PARKINSENSE
pip install -r requirements.txt
python run.py
```
*Or run Streamlit directly:*
```bash
streamlit run app_streamlit.py
```

#### 2. Launch the VocalAid Dysarthric Speech Recognition Platform:
```bash
cd DEMOOOO
pip install -r requirements.txt
run_app.bat
# or: python app.py --port 8080
```
Open **`http://localhost:8080`** in any browser.

---

## 👥 Contributors & Acknowledgements
- Developed for **ParkinSense** multimodal clinical screening and assistive AI.
- Datasets: UASpeech (University of Illinois), TORGO (University of Toronto), Parkinson Spiral Drawings.
- Base Model: `facebook/wav2vec2-base-960h` by Meta AI Research.
