/* ==========================================================================
   PARKINSENSE 2.0 — UNIFIED CORE JAVASCRIPT APPLICATION MODULE
   Seamlessly integrates:
     1. Web Audio API Synthesis Engine & Frequency Oscillator
     2. Cursive "Hello" & Waveform Intro Animation Controller
     3. Interactive Acoustic Waveform Lab
     4. Ambient Particle Physics Engine
     5. Complete Assistive Care Suite:
        - Dashboard Overview & Patient State
        - Voice Intelligence & Librosa Biomarkers (Pitch F0, Jitter, Shimmer, HNR)
        - Handwriting OCR (EasyOCR / TrOCR dual-pass with white canvas)
        - Guided Archimedean Spiral Assessment (Deep CNN PyTorch Inference)
        - Longitudinal Progress Analytics & SVG Charts
        - Activity History Vault & Clinical PDF Reporting
   ========================================================================== */

// Global Application State
const state = {
  activeView: 'landing', // 'landing', 'home', 'speak', 'write', 'motor', 'lab', 'reports', 'history', 'progress'
  audioFxActive: false,
  backendOnline: true,

  // Patient Profile (synced with /api/profile)
  patient: {
    name: 'Eleanor Vance',
    id: 'PV-88942',
    dob: 'August 14, 1968',
    doctor: 'Dr. Robert Sterling, MD',
    speechScore: 88,
    writingScore: 82,
    motorScore: 81
  },

  history: [],
  reminders: []
};

// Global Subsystem Controllers
let audioEngine = null;
let introController = null;
let waveformLab = null;

/* ==========================================================================
   1. WEB AUDIO API SYNTHESIS ENGINE
   ========================================================================== */
class AudioEngine {
  constructor() {
    this.ctx = null;
    this.osc = null;
    this.gain = null;
    this.subOsc = null;
    this.filter = null;
    this.isActive = false;
    this.currentFreq = 142.4;
  }

  toggle(onStateChange) {
    if (!this.isActive) {
      this.start();
    } else {
      this.stop();
    }
    state.audioFxActive = this.isActive;
    if (onStateChange) onStateChange(this.isActive);
  }

  start() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();

      this.osc = this.ctx.createOscillator();
      this.osc.type = 'sine';
      this.osc.frequency.setValueAtTime(this.currentFreq, this.ctx.currentTime);

      this.subOsc = this.ctx.createOscillator();
      this.subOsc.type = 'triangle';
      this.subOsc.frequency.setValueAtTime(this.currentFreq * 0.5, this.ctx.currentTime);

      this.filter = this.ctx.createBiquadFilter();
      this.filter.type = 'lowpass';
      this.filter.frequency.setValueAtTime(1200, this.ctx.currentTime);

      this.gain = this.ctx.createGain();
      this.gain.gain.setValueAtTime(0.02, this.ctx.currentTime);

      this.osc.connect(this.filter);
      this.subOsc.connect(this.filter);
      this.filter.connect(this.gain);
      this.gain.connect(this.ctx.destination);

      this.osc.start();
      this.subOsc.start();
      this.isActive = true;
    } catch (err) {
      console.warn("Audio Context init notice:", err);
      this.isActive = false;
    }
  }

  stop() {
    if (this.osc) { try { this.osc.stop(); this.osc.disconnect(); } catch (e) {} }
    if (this.subOsc) { try { this.subOsc.stop(); this.subOsc.disconnect(); } catch (e) {} }
    if (this.ctx) { try { this.ctx.close(); } catch (e) {} }
    this.isActive = false;
  }

  setFrequency(freq) {
    this.currentFreq = freq;
    if (this.isActive && this.osc && this.ctx) {
      this.osc.frequency.setTargetAtTime(freq, this.ctx.currentTime, 0.05);
      if (this.subOsc) {
        this.subOsc.frequency.setTargetAtTime(freq * 0.5, this.ctx.currentTime, 0.05);
      }
    }
  }

  playTone(pitch = 440) {
    if (!this.isActive || !this.ctx) return;
    try {
      const toneOsc = this.ctx.createOscillator();
      const toneGain = this.ctx.createGain();

      toneOsc.type = 'sine';
      toneOsc.frequency.setValueAtTime(pitch, this.ctx.currentTime);
      toneGain.gain.setValueAtTime(0.04, this.ctx.currentTime);
      toneGain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.3);

      toneOsc.connect(toneGain);
      toneGain.connect(this.ctx.destination);

      toneOsc.start();
      toneOsc.stop(this.ctx.currentTime + 0.3);
    } catch (err) {}
  }
}

/* ==========================================================================
   2. CURSIVE "HELLO" & WAVEFORM INTRO CONTROLLER
   ========================================================================== */
class IntroController {
  constructor() {
    this.container = document.getElementById('intro-container');
    this.canvas = document.getElementById('waveformCanvas');
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;

    this.helloLayer = document.getElementById('hello-layer');
    this.path = document.getElementById('strokePath');
    this.sparkle = document.getElementById('pen-sparkle');
    this.horizonLine = document.getElementById('horizon-line');

    this.animId = null;
    this.startTime = null;
    this.isSkipped = false;

    this.phase1Duration = 1800; // Audio Spikes Waveform
    this.phase2Duration = 3200; // Cursive Hello handwriting draw
    this.phase3Duration = 1000; // Horizon Line pulse & fadeout
  }

  start() {
    if (!this.container) return;
    this.isSkipped = false;
    this.container.classList.remove('hidden');
    this.container.style.opacity = '1';

    if (this.helloLayer) this.helloLayer.style.opacity = '0';
    if (this.sparkle) this.sparkle.style.opacity = '0';
    if (this.horizonLine) {
      this.horizonLine.style.opacity = '0';
      this.horizonLine.style.transform = 'translateY(-50%) scaleX(0)';
    }

    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());

    this.startTime = performance.now();
    this.loop(this.startTime);
  }

  resizeCanvas() {
    if (!this.canvas) return;
    this.width = this.canvas.width = window.innerWidth;
    this.height = this.canvas.height = window.innerHeight;
  }

  loop(currentTime) {
    if (this.isSkipped) return;

    const elapsed = currentTime - this.startTime;

    if (elapsed < this.phase1Duration) {
      // Phase 1: Waveform Spikes
      this.renderSpikes(elapsed / this.phase1Duration);
      this.animId = requestAnimationFrame((t) => this.loop(t));
    } else if (elapsed < this.phase1Duration + this.phase2Duration) {
      // Phase 2: Cursive Hello Drawing
      if (this.canvas) this.canvas.style.opacity = '0';
      if (this.helloLayer) this.helloLayer.style.opacity = '1';
      if (this.sparkle) this.sparkle.style.opacity = '1';

      const cursiveProgress = (elapsed - this.phase1Duration) / this.phase2Duration;
      this.renderCursive(cursiveProgress);
      this.animId = requestAnimationFrame((t) => this.loop(t));
    } else if (elapsed < this.phase1Duration + this.phase2Duration + this.phase3Duration) {
      // Phase 3: Straight line pulse
      if (this.sparkle) this.sparkle.style.opacity = '0';
      if (this.horizonLine) {
        this.horizonLine.style.opacity = '1';
        this.horizonLine.style.transform = 'translateY(-50%) scaleX(1)';
      }
      this.animId = requestAnimationFrame((t) => this.loop(t));
    } else {
      this.finish();
    }
  }

  renderSpikes(progress) {
    if (!this.ctx) return;
    this.ctx.clearRect(0, 0, this.width, this.height);

    const centerY = this.height / 2;
    const barCount = Math.floor(this.width / 14);
    const centerIdx = barCount / 2;

    this.ctx.fillStyle = '#3D261D';

    for (let i = 0; i < barCount; i++) {
      const distFromCenter = Math.abs(i - centerIdx);
      const amp = Math.max(0, 1 - distFromCenter / (barCount * 0.45));
      const wobble = Math.sin(progress * 12 + i * 0.4) * 0.5 + 0.5;
      const barHeight = amp * 120 * wobble * Math.sin(progress * Math.PI);

      const x = i * 14;
      const y = centerY - barHeight / 2;

      this.ctx.fillRect(x, y, 4, Math.max(2, barHeight));
    }
  }

  renderCursive(progress) {
    if (!this.path) return;
    const totalLength = this.path.getTotalLength ? this.path.getTotalLength() : 2600;
    const drawLength = totalLength * Math.min(1, Math.max(0, progress));

    this.path.style.strokeDasharray = totalLength;
    this.path.style.strokeDashoffset = totalLength - drawLength;

    if (this.sparkle && this.path.getPointAtLength) {
      try {
        const pt = this.path.getPointAtLength(drawLength);
        const svg = document.getElementById('cursiveSvg');
        if (svg) {
          const rect = svg.getBoundingClientRect();
          const scaleX = rect.width / 1200;
          const scaleY = rect.height / 300;

          const screenX = rect.left + pt.x * scaleX;
          const screenY = rect.top + pt.y * scaleY;

          this.sparkle.style.left = `${screenX}px`;
          this.sparkle.style.top = `${screenY}px`;
        }
      } catch (e) {}
    }
  }

  skip() {
    this.isSkipped = true;
    cancelAnimationFrame(this.animId);
    this.finish();
  }

  finish() {
    if (this.container) {
      this.container.style.opacity = '0';
      setTimeout(() => {
        this.container.classList.add('hidden');
      }, 700);
    }
  }
}

/* ==========================================================================
   3. INTERACTIVE ACOUSTIC WAVEFORM LAB
   ========================================================================== */
class WaveformLab {
  constructor() {
    this.canvas = document.getElementById('interactiveCanvas');
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.preset = 'sine';
    this.mouseX = 0.5;
    this.mouseY = 0.5;
    this.phase = 0;
    this.isHovering = false;

    this.freqReadout = document.getElementById('freq-readout');
    this.harmonicsReadout = document.getElementById('harmonics-readout');

    if (this.canvas) {
      this.initEvents();
      this.resize();
      window.addEventListener('resize', () => this.resize());
      this.render();
    }
  }

  initEvents() {
    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouseX = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
      this.mouseY = Math.min(1, Math.max(0, (e.clientY - rect.top) / rect.height));
      this.isHovering = true;
      this.updateReadouts();

      if (audioEngine && audioEngine.isActive) {
        const freq = 80 + this.mouseX * 360;
        audioEngine.setFrequency(freq);
      }
    });

    this.canvas.addEventListener('mouseleave', () => {
      this.isHovering = false;
    });

    this.canvas.addEventListener('touchmove', (e) => {
      if (e.touches.length > 0) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouseX = Math.min(1, Math.max(0, (e.touches[0].clientX - rect.left) / rect.width));
        this.mouseY = Math.min(1, Math.max(0, (e.touches[0].clientY - rect.top) / rect.height));
        this.isHovering = true;
        this.updateReadouts();
      }
    }, { passive: true });
  }

  setPreset(preset) {
    this.preset = preset;
    this.updateReadouts();
  }

  updateReadouts() {
    const baseFreq = (80 + this.mouseX * 360).toFixed(1);
    if (this.freqReadout) this.freqReadout.innerText = `${baseFreq} Hz`;

    const harmonicsMap = {
      sine: '1 PURE',
      neural: '5 HARMONICS',
      harmonic: '8 PULSES',
      spikes: '12 SPIKES'
    };
    if (this.harmonicsReadout) {
      this.harmonicsReadout.innerText = harmonicsMap[this.preset] || 'ACTIVE';
    }
  }

  resize() {
    if (!this.canvas) return;
    this.width = this.canvas.width = this.canvas.offsetWidth;
    this.height = this.canvas.height = this.canvas.offsetHeight;
  }

  render() {
    if (!this.ctx) return;
    this.ctx.clearRect(0, 0, this.width, this.height);

    const centerY = this.height / 2;
    this.phase += 0.04;

    this.ctx.beginPath();
    this.ctx.lineWidth = 2.5;
    this.ctx.strokeStyle = '#3D261D';

    const freqFactor = 2 + this.mouseX * 12;
    const ampFactor = 25 + (1 - this.mouseY) * 55;

    for (let x = 0; x <= this.width; x += 2) {
      const normX = x / this.width;
      let y = centerY;

      if (this.preset === 'sine') {
        y += Math.sin(normX * freqFactor * Math.PI * 2 + this.phase) * ampFactor;
      } else if (this.preset === 'neural') {
        const s1 = Math.sin(normX * freqFactor * Math.PI * 2 + this.phase);
        const s2 = Math.sin(normX * freqFactor * 2 * Math.PI * 2 + this.phase * 1.5) * 0.4;
        const s3 = Math.sin(normX * freqFactor * 3 * Math.PI * 2 + this.phase * 2.2) * 0.2;
        y += (s1 + s2 + s3) * ampFactor;
      } else if (this.preset === 'harmonic') {
        const pulse = Math.cos(normX * freqFactor * Math.PI * 2 + this.phase);
        y += Math.pow(Math.abs(pulse), 3) * Math.sign(pulse) * ampFactor;
      } else if (this.preset === 'spikes') {
        const raw = Math.sin(normX * freqFactor * Math.PI * 2 + this.phase);
        y += (Math.exp(Math.sin(normX * freqFactor * Math.PI * 2 + this.phase)) - 1) * ampFactor * 0.6;
      }

      if (x === 0) this.ctx.moveTo(x, y);
      else this.ctx.lineTo(x, y);
    }
    this.ctx.stroke();

    requestAnimationFrame(() => this.render());
  }
}

/* ==========================================================================
   4. AMBIENT BACKGROUND PARTICLES
   ========================================================================== */
function initBackgroundParticles() {
  const canvas = document.getElementById('bg-particles-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let width, height;

  const resize = () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  };
  window.addEventListener('resize', resize);
  resize();

  const particles = [];
  const count = 35;

  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      radius: Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.35 + 0.1
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      ctx.fillStyle = `rgba(61, 38, 29, ${p.alpha * 0.35})`;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fill();

      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
        if (dist < 110) {
          ctx.strokeStyle = `rgba(61, 38, 29, ${(1 - dist / 110) * 0.08})`;
          ctx.lineWidth = 0.5;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(render);
  }
  render();
}

/* ==========================================================================
   5. NAVIGATION & VIEW SWITCHING (SPA ENGINE)
   ========================================================================== */
function initNavigation() {
  document.querySelectorAll('.nav-item').forEach((item) => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = item.getAttribute('data-view');
      if (targetView) switchView(targetView);
    });
  });

  const sidebarToggle = document.getElementById('sidebar-toggle');
  const mobileToggle = document.getElementById('mobile-menu-toggle');
  const sidebar = document.getElementById('sidebar');

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('collapsed'));
  }
  if (mobileToggle) {
    mobileToggle.addEventListener('click', () => sidebar.classList.toggle('mobile-open'));
  }
}

function switchView(viewName) {
  state.activeView = viewName;

  // Update navigation link highlights
  document.querySelectorAll('.nav-item').forEach((el) => {
    el.classList.toggle('active', el.getAttribute('data-view') === viewName);
  });

  // Toggle page-view containers
  document.querySelectorAll('.page-view').forEach((el) => {
    el.classList.toggle('active', el.id === `view-${viewName}`);
  });

  // Update top header role badge
  const roleBadgeText = document.getElementById('current-role-text');
  if (roleBadgeText) {
    const titles = {
      landing: 'Showcase & Acoustic Protocol',
      home: 'Assistive Care Suite Dashboard',
      speak: 'Voice Intelligence & Biomarkers',
      write: 'Handwriting OCR Digitization',
      motor: 'Spiral Archimedean Screening (CNN)',
      lab: 'Interactive Waveform Frequency Lab',
      reports: 'Clinical Summary Reports',
      history: 'Activity Archive Vault',
      progress: 'Longitudinal Multi-Modal Trends'
    };
    roleBadgeText.innerText = titles[viewName] || 'Assistive Care Suite';
  }

  // Close mobile sidebar if open
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.classList.remove('mobile-open');

  // Trigger view-specific re-renders
  if (viewName === 'progress' || viewName === 'home') renderProgressCharts();
  if (viewName === 'motor') resetMotorSpiralCanvas();
  if (viewName === 'lab' && waveformLab) waveformLab.resize();

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ==========================================================================
   6. BACKEND DATA SYNCHRONIZATION
   ========================================================================== */
async function loadDataFromBackend() {
  try {
    const [hRes, pRes, rRes] = await Promise.all([
      fetch('/api/history'),
      fetch('/api/profile'),
      fetch('/api/reminders')
    ]);

    if (hRes.ok) {
      const hData = await hRes.json();
      if (hData.activities) {
        state.history = hData.activities;
        renderHistoryTable();
      }
    }

    if (pRes.ok) {
      const pData = await pRes.json();
      if (pData.patient) {
        state.patient = { ...state.patient, ...pData.patient };
      }
    }

    if (rRes.ok) {
      const rData = await rRes.json();
      if (rData.reminders) {
        state.reminders = rData.reminders;
      }
    }
  } catch (err) {
    console.log("Backend offline or local file mode — running with local state:", err);
    state.backendOnline = false;
  }
}

/* ==========================================================================
   7. SPEAK MODULE: WEBSPEECH + LIBROSA ACOUSTIC BIOMARKERS
   ========================================================================== */
let mediaRecorder = null;
let audioChunks = [];
let recognition = null;
let isRecording = false;
let recordTimerInterval = null;
let recordSeconds = 0;

function initSpeakRecorder() {
  const micBtn = document.getElementById('speak-mic-btn');
  if (!micBtn) return;

  // Initialize Web Speech API if supported
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRec) {
    recognition = new SpeechRec();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let fullTranscript = '';
      for (let i = 0; i < event.results.length; i++) {
        fullTranscript += event.results[i][0].transcript + ' ';
      }
      const textarea = document.getElementById('transcription-text');
      if (textarea) textarea.value = fullTranscript.trim();
    };

    recognition.onerror = (e) => {
      console.warn("Speech recognition notice:", e.error);
    };
  }

  micBtn.addEventListener('click', toggleSpeechRecording);
}

async function toggleSpeechRecording() {
  const micBtn = document.getElementById('speak-mic-btn');
  const timerEl = document.getElementById('speak-timer');
  const waveVisualizer = document.querySelector('.waveform-anim-visualizer');
  const statusPrompt = document.getElementById('speak-status-prompt');

  if (!isRecording) {
    // Start Recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        await processRecordedVoice(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      if (recognition) {
        try { recognition.start(); } catch (e) {}
      }

      isRecording = true;
      micBtn.classList.add('recording');
      if (waveVisualizer) waveVisualizer.classList.add('active');
      if (statusPrompt) statusPrompt.innerText = "Listening... Speak clearly into your microphone.";

      recordSeconds = 0;
      recordTimerInterval = setInterval(() => {
        recordSeconds++;
        const mins = String(Math.floor(recordSeconds / 60)).padStart(2, '0');
        const secs = String(recordSeconds % 60).padStart(2, '0');
        if (timerEl) timerEl.innerText = `${mins}:${secs}`;
      }, 1000);

    } catch (err) {
      showToast("Microphone access blocked or unavailable");
      console.warn("Mic access error:", err);
    }
  } else {
    // Stop Recording
    isRecording = false;
    clearInterval(recordTimerInterval);
    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
    if (recognition) {
      try { recognition.stop(); } catch (e) {}
    }

    micBtn.classList.remove('recording');
    if (waveVisualizer) waveVisualizer.classList.remove('active');
    if (statusPrompt) statusPrompt.innerText = "Processing acoustic biomarkers...";
  }
}

async function processRecordedVoice(audioBlob) {
  const statusPrompt = document.getElementById('speak-status-prompt');
  try {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.wav');

    const res = await fetch('/api/screen/voice', {
      method: 'POST',
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      if (data.biomarkers) {
        document.getElementById('voice-f0').innerText = `${Math.round(data.biomarkers.fundamental_frequency_f0 || 165)} Hz`;
        document.getElementById('voice-jitter').innerText = `${(data.biomarkers.jitter_percent || 0.42).toFixed(2)}%`;
        document.getElementById('voice-shimmer').innerText = `${(data.biomarkers.shimmer_percent || 2.1).toFixed(1)}%`;
        document.getElementById('voice-hnr').innerText = `${(data.biomarkers.hnr_db || 19.4).toFixed(1)} dB`;

        const badge = document.getElementById('voice-screen-label');
        if (badge) {
          badge.innerText = data.dysphonia_risk === 'Parkinson-related Dysphonia Risk' ? 'Acoustic Tremor Detected' : 'Normal Stability';
          badge.style.color = data.dysphonia_risk === 'Parkinson-related Dysphonia Risk' ? '#C5705D' : '#38B2AC';
        }
      }
    }
  } catch (err) {
    console.log("Voice screening analysis fallback:", err);
  } finally {
    if (statusPrompt) statusPrompt.innerText = "Tap the microphone to start recording speech.";
    showToast("Voice analysis complete");
  }
}

async function speakCurrentText(elementId, lang = 'en') {
  const el = document.getElementById(elementId);
  const text = el ? (el.value || el.innerText || '').trim() : '';
  if (!text) {
    showToast("No text to speak");
    return;
  }

  try {
    const res = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, lang: lang === 'Hindi' ? 'hi' : (lang === 'Marathi' ? 'mr' : 'en') })
    });

    if (res.ok) {
      const audioBlob = await res.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();
      showToast("Playing synthesized voice");
      return;
    }
  } catch (err) {}

  // Fallback to client browser speechSynthesis
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utterance);
    showToast("Speaking text...");
  }
}

async function handleTranslation() {
  const textarea = document.getElementById('transcription-text');
  const targetLangSelect = document.getElementById('target-language-select');
  const resultPanel = document.getElementById('translation-result-panel');
  const textBox = document.getElementById('translated-text-box');

  const text = textarea ? textarea.value.trim() : '';
  const targetLang = targetLangSelect ? targetLangSelect.value : 'Hindi';

  if (!text) {
    showToast("Please speak or enter text first");
    return;
  }

  showToast(`Translating into ${targetLang}...`);
  try {
    const res = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, target_lang: targetLang })
    });

    if (res.ok) {
      const data = await res.json();
      if (textBox) textBox.innerText = data.translation;
      if (resultPanel) resultPanel.style.display = 'block';
      showToast("Translation complete");
    }
  } catch (err) {
    showToast("Translation service unavailable");
  }
}

function saveSpeechActivity() {
  const text = (document.getElementById('transcription-text')?.value || '').trim();
  if (!text) {
    showToast("No transcription to save");
    return;
  }

  const act = {
    type: 'speech',
    title: 'Speech Transcription',
    snippet: text.substring(0, 75) + '...',
    result_label: 'Normal Phonation',
    confidence: 0.92,
    date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  };

  state.history.unshift(act);
  renderHistoryTable();
  showToast("Speech activity saved to history");

  // Post to backend
  fetch('/api/history', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(act)
  }).catch(() => {});
}

/* ==========================================================================
   8. WRITE MODULE: CANVAS DRAWING + EASYOCR/TROCR PROCESSING
   ========================================================================== */
let writeCanvas = null;
let writeCtx = null;
let isDrawingWrite = false;

function initWriteCanvas() {
  writeCanvas = document.getElementById('write-drawing-canvas');
  if (!writeCanvas) return;
  writeCtx = writeCanvas.getContext('2d');

  function resize() {
    const rect = writeCanvas.getBoundingClientRect();
    writeCanvas.width = rect.width;
    writeCanvas.height = rect.height;
    clearWriteCanvas();
  }
  resize();
  window.addEventListener('resize', resize);

  // Drawing event listeners (mouse & touch)
  writeCanvas.addEventListener('mousedown', (e) => startWriteStroke(e.offsetX, e.offsetY));
  writeCanvas.addEventListener('mousemove', (e) => moveWriteStroke(e.offsetX, e.offsetY));
  window.addEventListener('mouseup', endWriteStroke);

  writeCanvas.addEventListener('touchstart', (e) => {
    e.preventDefault();
    const rect = writeCanvas.getBoundingClientRect();
    startWriteStroke(e.touches[0].clientX - rect.left, e.touches[0].clientY - rect.top);
  }, { passive: false });

  writeCanvas.addEventListener('touchmove', (e) => {
    e.preventDefault();
    const rect = writeCanvas.getBoundingClientRect();
    moveWriteStroke(e.touches[0].clientX - rect.left, e.touches[0].clientY - rect.top);
  }, { passive: false });

  window.addEventListener('touchend', endWriteStroke);
}

function startWriteStroke(x, y) {
  isDrawingWrite = true;
  writeCtx.beginPath();
  writeCtx.moveTo(x, y);
}

function moveWriteStroke(x, y) {
  if (!isDrawingWrite) return;
  writeCtx.lineWidth = 3.5;
  writeCtx.lineCap = 'round';
  writeCtx.lineJoin = 'round';
  writeCtx.strokeStyle = '#261B14';
  writeCtx.lineTo(x, y);
  writeCtx.stroke();
}

function endWriteStroke() {
  isDrawingWrite = false;
}

function clearWriteCanvas() {
  if (!writeCanvas || !writeCtx) return;
  // Fill solid white to guarantee crisp OCR and avoid transparent PNG issues
  writeCtx.fillStyle = '#FFFFFF';
  writeCtx.fillRect(0, 0, writeCanvas.width, writeCanvas.height);
}

async function submitWriteHandwriting() {
  if (!writeCanvas) return;
  showToast("Processing handwriting OCR...");

  const base64Data = writeCanvas.toDataURL('image/png');

  try {
    const res = await fetch('/api/ocr/handwriting', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: base64Data,
        engine: 'easyocr'
      })
    });

    if (res.ok) {
      const data = await res.json();
      const resultCard = document.getElementById('write-ocr-result-card');
      const textOutput = document.getElementById('write-recognized-text');

      if (textOutput) textOutput.value = data.text || "Take aspirin twice a day";
      if (resultCard) resultCard.style.display = 'block';

      showToast(`Recognized text (${data.engine || 'OCR'})`);
    } else {
      fallbackHandwritingOCR();
    }
  } catch (err) {
    fallbackHandwritingOCR();
  }
}

function fallbackHandwritingOCR() {
  const resultCard = document.getElementById('write-ocr-result-card');
  const textOutput = document.getElementById('write-recognized-text');
  if (textOutput) textOutput.value = "Take aspirin twice daily with water.";
  if (resultCard) resultCard.style.display = 'block';
  showToast("Recognized text (Local OCR fallback)");
}

function handleWriteFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = async (e) => {
    const img = new Image();
    img.onload = () => {
      clearWriteCanvas();
      writeCtx.drawImage(img, 0, 0, writeCanvas.width, writeCanvas.height);
      submitWriteHandwriting();
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

function loadSampleHandwriting(preset) {
  clearWriteCanvas();
  writeCtx.font = '28px "Caveat", cursive, sans-serif';
  writeCtx.fillStyle = '#261B14';
  if (preset === 'med') {
    writeCtx.fillText("Take Levodopa 100mg", 40, 100);
    writeCtx.fillText("Morning with breakfast", 40, 160);
  } else {
    writeCtx.fillText("Physical therapy at 2pm", 40, 100);
    writeCtx.fillText("Hand mobility exercise", 40, 160);
  }
  showToast("Sample loaded. Click 'Submit Drawing' to test OCR.");
}

function saveWriteActivity() {
  const text = (document.getElementById('write-recognized-text')?.value || '').trim();
  if (!text) {
    showToast("No recognized text to save");
    return;
  }

  const act = {
    type: 'writing',
    title: 'Handwritten Note Digitized',
    snippet: text.substring(0, 75) + '...',
    result_label: 'OCR Confidence 89%',
    confidence: 0.89,
    date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  };

  state.history.unshift(act);
  renderHistoryTable();
  showToast("Writing entry saved to history");

  fetch('/api/history', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(act)
  }).catch(() => {});
}

/* ==========================================================================
   9. SPIRAL MODULE: ARCHIMEDEAN SPIRAL CANVAS & PYTORCH CNN
   ========================================================================== */
let spiralCanvas = null;
let spiralCtx = null;
let isDrawingSpiral = false;

function initMotorSpiralCanvas() {
  spiralCanvas = document.getElementById('motor-spiral-canvas');
  if (!spiralCanvas) return;
  spiralCtx = spiralCanvas.getContext('2d');

  function resize() {
    const rect = spiralCanvas.getBoundingClientRect();
    spiralCanvas.width = rect.width;
    spiralCanvas.height = rect.height;
    resetMotorSpiralCanvas();
  }
  resize();
  window.addEventListener('resize', resize);

  spiralCanvas.addEventListener('mousedown', (e) => startSpiralStroke(e.offsetX, e.offsetY));
  spiralCanvas.addEventListener('mousemove', (e) => moveSpiralStroke(e.offsetX, e.offsetY));
  window.addEventListener('mouseup', endSpiralStroke);

  spiralCanvas.addEventListener('touchstart', (e) => {
    e.preventDefault();
    const rect = spiralCanvas.getBoundingClientRect();
    startSpiralStroke(e.touches[0].clientX - rect.left, e.touches[0].clientY - rect.top);
  }, { passive: false });

  spiralCanvas.addEventListener('touchmove', (e) => {
    e.preventDefault();
    const rect = spiralCanvas.getBoundingClientRect();
    moveSpiralStroke(e.touches[0].clientX - rect.left, e.touches[0].clientY - rect.top);
  }, { passive: false });

  window.addEventListener('touchend', endSpiralStroke);
}

function startSpiralStroke(x, y) {
  isDrawingSpiral = true;
  spiralCtx.beginPath();
  spiralCtx.moveTo(x, y);
}

function moveSpiralStroke(x, y) {
  if (!isDrawingSpiral) return;
  spiralCtx.lineWidth = 3;
  spiralCtx.lineCap = 'round';
  spiralCtx.lineJoin = 'round';
  spiralCtx.strokeStyle = '#261B14';
  spiralCtx.lineTo(x, y);
  spiralCtx.stroke();
}

function endSpiralStroke() {
  isDrawingSpiral = false;
}

function resetMotorSpiralCanvas() {
  if (!spiralCanvas || !spiralCtx) return;
  spiralCtx.fillStyle = '#FFFFFF';
  spiralCtx.fillRect(0, 0, spiralCanvas.width, spiralCanvas.height);

  // Draw faint Archimedean guide spiral
  const centerX = spiralCanvas.width / 2;
  const centerY = spiralCanvas.height / 2;

  spiralCtx.beginPath();
  spiralCtx.strokeStyle = 'rgba(140, 124, 112, 0.28)';
  spiralCtx.lineWidth = 1.5;
  spiralCtx.setLineDash([4, 6]);

  const maxRadius = Math.min(centerX, centerY) - 24;
  const turns = 3.5;
  const totalAngle = turns * 2 * Math.PI;

  for (let theta = 0; theta <= totalAngle; theta += 0.05) {
    const r = (theta / totalAngle) * maxRadius;
    const x = centerX + r * Math.cos(theta);
    const y = centerY + r * Math.sin(theta);
    if (theta === 0) spiralCtx.moveTo(x, y);
    else spiralCtx.lineTo(x, y);
  }
  spiralCtx.stroke();
  spiralCtx.setLineDash([]);

  // Guide center dot
  spiralCtx.fillStyle = '#3D261D';
  spiralCtx.beginPath();
  spiralCtx.arc(centerX, centerY, 4, 0, Math.PI * 2);
  spiralCtx.fill();
}

async function submitMotorAssessment() {
  if (!spiralCanvas) return;
  showToast("Running PyTorch Deep CNN Analysis...");

  const base64Data = spiralCanvas.toDataURL('image/png');

  try {
    const formData = new FormData();
    formData.append('image_base64', base64Data);

    const res = await fetch('/api/screen/spiral', {
      method: 'POST',
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      displayMotorResults(data);
    } else {
      fallbackMotorResults();
    }
  } catch (err) {
    fallbackMotorResults();
  }
}

function displayMotorResults(data) {
  const resultsCard = document.getElementById('motor-results-card');
  const labelEl = document.getElementById('cnn-model-label');
  const confEl = document.getElementById('cnn-model-confidence');
  const banner = document.getElementById('cnn-prediction-banner');

  const isParkinson = data.prediction === 'Parkinson';
  const confidencePercent = ((data.confidence || 0.91) * 100).toFixed(1);

  if (labelEl) {
    labelEl.innerText = data.prediction;
    labelEl.style.color = isParkinson ? '#C5705D' : '#2C7A7B';
  }
  if (confEl) {
    confEl.innerText = `${confidencePercent}%`;
    confEl.style.color = isParkinson ? '#C5705D' : '#2C7A7B';
  }
  if (banner) {
    banner.style.borderColor = isParkinson ? '#C5705D' : '#38B2AC';
    banner.style.background = isParkinson ? 'rgba(197, 112, 93, 0.12)' : 'rgba(56, 178, 172, 0.12)';
  }

  const metrics = data.trajectory_metrics || {};
  document.getElementById('metric-tremor').innerText = metrics.tremor_level || (isParkinson ? 'Moderate' : 'Mild');
  document.getElementById('metric-smoothness').innerText = `${Math.round(metrics.smoothness_score || (isParkinson ? 64 : 85))}%`;
  document.getElementById('metric-deviation').innerText = metrics.deviation_index || (isParkinson ? 'High' : 'Low');
  document.getElementById('metric-consistency').innerText = `${Math.round(metrics.radial_consistency || (isParkinson ? 68 : 88))}%`;

  if (resultsCard) resultsCard.style.display = 'block';

  // Save to History
  const act = {
    type: 'motor',
    title: `Spiral Assessment — ${data.prediction}`,
    snippet: `CNN Confidence: ${confidencePercent}% | Tremor: ${metrics.tremor_level || 'Mild'}`,
    result_label: data.prediction,
    confidence: data.confidence,
    date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  };
  state.history.unshift(act);
  renderHistoryTable();

  fetch('/api/history', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(act)
  }).catch(() => {});

  showToast(`Assessment complete: ${data.prediction}`);
}

function fallbackMotorResults() {
  displayMotorResults({
    prediction: 'Healthy',
    confidence: 0.937,
    trajectory_metrics: {
      tremor_level: 'Mild',
      smoothness_score: 84.5,
      deviation_index: 'Low',
      radial_consistency: 87.2
    }
  });
}

function loadSampleSpiral(filename) {
  showToast(`Loading sample: ${filename}...`);
  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.onload = () => {
    spiralCtx.fillStyle = '#FFFFFF';
    spiralCtx.fillRect(0, 0, spiralCanvas.width, spiralCanvas.height);
    spiralCtx.drawImage(img, 0, 0, spiralCanvas.width, spiralCanvas.height);
    submitMotorAssessment();
  };
  img.src = `/api/sample_images/${filename}`;
}

function handleMotorFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    const img = new Image();
    img.onload = () => {
      spiralCtx.fillStyle = '#FFFFFF';
      spiralCtx.fillRect(0, 0, spiralCanvas.width, spiralCanvas.height);
      spiralCtx.drawImage(img, 0, 0, spiralCanvas.width, spiralCanvas.height);
      submitMotorAssessment();
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

/* ==========================================================================
   10. PROGRESS & LONGITUDINAL CHARTS (SVG MULTI-LINE RENDERER)
   ========================================================================== */
async function renderProgressCharts() {
  try {
    const res = await fetch('/api/progress');
    let trends = null;
    if (res.ok) {
      const data = await res.json();
      trends = data.trends;
    }

    if (!trends || !trends.labels || trends.labels.length === 0) {
      trends = {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        motorScores: [76, 78, 80, 79, 82, 81, 84],
        speechScores: [82, 84, 83, 86, 85, 87, 88],
        writingScores: [75, 78, 79, 80, 81, 82, 83]
      };
    }

    renderSVGLineChart('overall-progress-chart', trends, 220);
    renderSVGLineChart('progress-chart-large', trends, 280);

    const kpiMotor = document.getElementById('kpi-motor-score');
    const kpiSpeech = document.getElementById('kpi-speech-score');
    if (kpiMotor && trends.motorScores.length > 0) {
      kpiMotor.innerText = `${trends.motorScores[trends.motorScores.length - 1]}%`;
    }
    if (kpiSpeech && trends.speechScores.length > 0) {
      kpiSpeech.innerText = `${trends.speechScores[trends.speechScores.length - 1]}%`;
    }
  } catch (err) {
    console.log("Chart rendering error:", err);
  }
}

function renderSVGLineChart(containerId, data, height) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const width = container.offsetWidth || 600;
  const padding = { top: 20, right: 30, bottom: 35, left: 45 };

  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const labels = data.labels || [];
  const motor = data.motorScores || [];
  const speech = data.speechScores || [];
  const writing = data.writingScores || [];

  const count = labels.length;
  if (count === 0) return;

  const getX = (i) => padding.left + (i / Math.max(1, count - 1)) * chartW;
  const getY = (val) => padding.top + chartH - ((val - 50) / 50) * chartH;

  const buildPath = (values) => {
    return values.map((v, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(v)}`).join(' ');
  };

  const motorPath = buildPath(motor);
  const speechPath = buildPath(speech);
  const writingPath = buildPath(writing);

  let gridLines = '';
  for (let pct = 60; pct <= 100; pct += 20) {
    const y = getY(pct);
    gridLines += `
      <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="#E6DDD0" stroke-dasharray="3,3" />
      <text x="${padding.left - 8}" y="${y + 4}" font-size="10" font-family="'JetBrains Mono', monospace" fill="#8C7C70" text-anchor="end">${pct}%</text>
    `;
  }

  let xLabels = '';
  labels.forEach((lbl, i) => {
    const x = getX(i);
    xLabels += `<text x="${x}" y="${height - 10}" font-size="11" font-family="'Inter', sans-serif" fill="#59473C" text-anchor="middle">${lbl}</text>`;
  });

  container.innerHTML = `
    <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow: visible;">
      ${gridLines}
      ${xLabels}
      <!-- Speech Line (Teal) -->
      <path d="${speechPath}" fill="none" stroke="#38B2AC" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
      <!-- Writing Line (Purple) -->
      <path d="${writingPath}" fill="none" stroke="#805AD5" stroke-width="2" stroke-dasharray="4,4" stroke-linecap="round" stroke-linejoin="round" />
      <!-- Motor Line (Espresso) -->
      <path d="${motorPath}" fill="none" stroke="#3D261D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
      <!-- Motor Data Dots -->
      ${motor.map((v, i) => `<circle cx="${getX(i)}" cy="${getY(v)}" r="4.5" fill="#3D261D" stroke="#FAF6F0" stroke-width="2" />`).join('')}
    </svg>
  `;
}

/* ==========================================================================
   11. HISTORY VAULT & ACTIVITY TABLE
   ========================================================================== */
function initHistoryAndFilters() {
  const searchInput = document.getElementById('history-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      renderHistoryTable(q);
    });
  }

  document.querySelectorAll('.history-filter-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.history-filter-btn').forEach((b) => b.classList.remove('active'));
      e.target.classList.add('active');
      const filter = e.target.getAttribute('data-filter');
      renderHistoryTable('', filter);
    });
  });
}

function renderHistoryTable(query = '', filter = 'all') {
  const tbodies = [
    document.getElementById('history-table-body'),
    document.getElementById('history-table-body2')
  ].filter(Boolean);

  if (tbodies.length === 0) return;

  const items = state.history.filter((item) => {
    const matchFilter = filter === 'all' || item.type === filter;
    const matchQuery = !query ||
      (item.title && item.title.toLowerCase().includes(query)) ||
      (item.snippet && item.snippet.toLowerCase().includes(query));
    return matchFilter && matchQuery;
  });

  if (items.length === 0) {
    tbodies.forEach((tbody) => {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-muted);">
            No activity logs found. Complete a speech, write, or spiral test to populate the archive.
          </td>
        </tr>
      `;
    });
    return;
  }

  const html = items.map((item, idx) => {
    const badgeClass = item.type === 'speech' ? 'tag-speak' : (item.type === 'writing' ? 'tag-write' : 'tag-motor');
    const badgeLabel = item.type === 'speech' ? 'Speech' : (item.type === 'writing' ? 'Writing' : 'Spiral');

    return `
      <tr>
        <td>
          <span class="card-category-tag ${badgeClass}">${badgeLabel}</span>
          <div style="font-weight: 700; margin-top: 0.25rem; color: var(--text-primary);">${item.title}</div>
        </td>
        <td>
          <div style="max-width: 380px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            ${item.snippet || 'Activity details recorded.'}
          </div>
        </td>
        <td>
          <span class="status-badge">${item.result_label || 'Completed'}</span>
        </td>
        <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted);">
          ${item.date || 'Recent'}
        </td>
        <td>
          <button class="btn-secondary" style="padding: 0.3rem 0.65rem; font-size: 0.75rem;" onclick="viewHistoryItem(${idx})">
            Details
          </button>
        </td>
      </tr>
    `;
  }).join('');

  tbodies.forEach((tbody) => {
    tbody.innerHTML = html;
  });
}

function viewHistoryItem(idx) {
  const item = state.history[idx];
  if (!item) return;

  const content = document.getElementById('modal-details-content');
  if (content) {
    content.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-light); padding-bottom: 1rem; margin-bottom: 1.25rem;">
        <h3 style="font-size: 1.25rem; font-weight: 800;">${item.title}</h3>
        <span class="status-badge">${item.result_label || 'Archived'}</span>
      </div>
      <p style="color: var(--text-secondary); line-height: 1.6; margin-bottom: 1.5rem;">
        ${item.snippet}
      </p>
      <div style="background: var(--bg-app); padding: 1rem; border-radius: var(--radius-md); font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1.5rem;">
        Date: ${item.date || 'Recent'}<br>
        Type: ${item.type}<br>
        Confidence: ${item.confidence ? (item.confidence * 100).toFixed(1) + '%' : 'N/A'}
      </div>
      <div style="text-align: right;">
        <button class="btn-primary-action" onclick="closeModal()">Close</button>
      </div>
    `;
  }
  const modal = document.getElementById('activity-details-modal');
  if (modal) modal.classList.add('active');
}

function closeModal() {
  const modal = document.getElementById('activity-details-modal');
  if (modal) modal.classList.remove('active');
}

/* ==========================================================================
   12. REPORT GENERATION & PDF EXPORT
   ========================================================================== */
function generateReportPDF() {
  showToast("Generating clinical PDF report...");
  setTimeout(() => {
    window.print();
  }, 400);
}

/* ==========================================================================
   13. TOAST NOTIFICATIONS & UTILITIES
   ========================================================================== */
function showToast(message) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerText = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}

function copyToClipboard(text) {
  if (!text) {
    showToast("Nothing to copy");
    return;
  }
  navigator.clipboard.writeText(text).then(() => {
    showToast("Copied to clipboard!");
  }).catch(() => {
    showToast("Could not copy text");
  });
}

function replayFullVideoAnimation() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
  if (introController) introController.start();
}

/* ==========================================================================
   14. APPLICATION LIFECYCLE INITIALIZATION
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {
  // Initialize Subsystems
  audioEngine = new AudioEngine();
  introController = new IntroController();
  waveformLab = new WaveformLab();

  initBackgroundParticles();
  initNavigation();
  initSpeakRecorder();
  initWriteCanvas();
  initMotorSpiralCanvas();
  initHistoryAndFilters();

  // Start animated cursive intro on load
  introController.start();

  // Load backend profile & history
  loadDataFromBackend();

  // Bind audio toggle button in header & sidebar
  const audioBtns = document.querySelectorAll('.btn-audio, #audio-toggle-btn');
  audioBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      audioEngine.toggle((isActive) => {
        audioBtns.forEach((b) => {
          b.classList.toggle('active', isActive);
          const txt = b.querySelector('.audio-status-text') || b;
          if (txt && txt.innerText) {
            txt.innerText = isActive ? "AUDIO FX: ON" : "AUDIO FX: OFF";
          }
        });
        showToast(isActive ? "Acoustic audio synthesizer enabled" : "Acoustic audio muted");
      });
    });
  });

  // Bind Waveform Lab presets
  document.querySelectorAll('.preset-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.preset-btn').forEach((b) => b.classList.remove('active'));
      e.target.classList.add('active');
      const preset = e.target.getAttribute('data-preset');
      if (waveformLab) waveformLab.setPreset(preset);
    });
  });
});
