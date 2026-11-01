/* ==========================================================================
   Voice Intelligence // Landing Page Unified Script Module
   Encapsulates Audio Engine, Intro Sequence, Waveform Lab, and UI Controls
   ========================================================================== */

// Global App State & Controllers
let audioEngine = null;
let introController = null;
let waveformLab = null;
let uiController = null;

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
      console.warn("Audio Context initialization notice:", err);
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
    } catch (e) {}
  }
}

/* ==========================================================================
   2. SEAMLESS INTRO ANIMATION CONTROLLER
   Audio Waveform Spikes -> Collapse -> Cursive "Hello" Stroke -> Straight Line Continuation
   ========================================================================== */
class IntroController {
  constructor() {
    this.container = document.getElementById('intro-container');
    this.canvas = document.getElementById('waveformCanvas');
    this.helloLayer = document.getElementById('hello-layer');
    this.sliderTrack = document.getElementById('slider-track');
    this.strokePath = document.getElementById('strokePath');
    this.horizonLine = document.getElementById('horizon-line');
    this.penSparkle = document.getElementById('pen-sparkle');
    this.landingPage = document.getElementById('landing-page');

    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.width = 0;
    this.height = 0;

    this.animFrame = null;
    this.startTime = null;
    this.phase = 0;
    this.collapseProgress = 0;
    this.isFinished = false;

    this.init();
  }

  init() {
    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());
  }

  resizeCanvas() {
    if (!this.canvas) return;
    this.width = this.canvas.width = window.innerWidth;
    this.height = this.canvas.height = window.innerHeight;
  }

  start() {
    this.isFinished = false;
    this.startTime = null;
    this.phase = 0;
    this.collapseProgress = 0;

    if (this.container) {
      this.container.style.display = 'flex';
      this.container.style.opacity = '1';
    }
    if (this.canvas) this.canvas.style.opacity = '1';
    if (this.helloLayer) this.helloLayer.style.opacity = '0';
    if (this.horizonLine) this.horizonLine.style.opacity = '0';
    if (this.sliderTrack) this.sliderTrack.style.transform = 'translateX(0px)';
    if (this.strokePath) this.strokePath.classList.remove('drawn');
    if (this.penSparkle) this.penSparkle.style.opacity = '0';

    this.resizeCanvas();
    this.animFrame = requestAnimationFrame((ts) => this.drawWaveform(ts));
  }

  // Phase 1 & 2: Audio Frequency Waveform Spike Modulation & Collapse onto Horizontal Baseline
  drawWaveform(timestamp) {
    if (!this.startTime) this.startTime = timestamp;
    const elapsed = timestamp - this.startTime;

    this.ctx.fillStyle = '#FAF6F0';
    this.ctx.fillRect(0, 0, this.width, this.height);

    const midY = this.height / 2;
    const barCount = 130;
    const barSpacing = this.width / (barCount + 1);

    this.ctx.lineWidth = 3;
    this.ctx.strokeStyle = '#3D261D';
    this.ctx.beginPath();

    const collapseMultiplier = Math.max(0, 1 - this.collapseProgress);

    for (let i = 0; i <= barCount; i++) {
      const x = i * barSpacing;
      const norm = (i / barCount) * 2 - 1;
      const envelope = Math.exp(-norm * norm * 4.2);

      const f1 = Math.sin(i * 0.28 + this.phase * 0.14);
      const f2 = Math.cos(i * 0.52 - this.phase * 0.09);
      const f3 = Math.sin(i * 0.85 + this.phase * 0.18);

      let spike = 1.0;
      if (i % 5 === 0) spike = 1.5;
      if (i % 9 === 0) spike = 2.1;
      if (i % 14 === 0) spike = 1.8;

      const rawAmp = (f1 * 0.5 + f2 * 0.35 + f3 * 0.25) * envelope;
      const height = Math.max(1.5, Math.abs(rawAmp * 160 * spike * collapseMultiplier));

      this.ctx.moveTo(x, midY - height);
      this.ctx.lineTo(x, midY + height);
    }
    this.ctx.stroke();

    this.phase += 1.2;

    if (elapsed < 2000) {
      // Phase 1: Voice spikes active
      this.animFrame = requestAnimationFrame((ts) => this.drawWaveform(ts));
    } else if (elapsed < 2800) {
      // Phase 2: Collapse smoothly into single horizontal line
      this.collapseProgress = (elapsed - 2000) / 800;
      this.animFrame = requestAnimationFrame((ts) => this.drawWaveform(ts));
    } else {
      // Phase 3: Morph continuously into Cursive "hello" stroke
      this.collapseProgress = 1.0;
      this.ctx.clearRect(0, 0, this.width, this.height);
      this.startCursiveSequence();
    }
  }

  // Phase 3 & 4: Continuous Line Handwriting -> Zoom In -> Direct Dashboard Navigation
  startCursiveSequence() {
    this.canvas.style.opacity = '0';
    this.helloLayer.style.opacity = '1';

    // Trigger SVG stroke drawing & sparkling follower
    setTimeout(() => {
      this.strokePath.classList.add('drawn');
      this.animatePenSparkle();
    }, 100);

    // Zoom in hello line without shifting to the left
    setTimeout(() => {
      if (this.helloLayer) {
        this.helloLayer.style.transform = 'scale(1.35)';
        this.helloLayer.style.transition = 'transform 1200ms cubic-bezier(0.16, 1, 0.3, 1), opacity 800ms ease';
      }
    }, 2200);

    // Directly navigate to Dashboard
    setTimeout(() => {
      this.finishIntro();
    }, 3200);
  }

  animatePenSparkle() {
    if (!this.strokePath || !this.penSparkle) return;

    const totalLength = this.strokePath.getTotalLength();
    const duration = 2200;
    const startTime = performance.now();
    this.penSparkle.style.opacity = '1';

    const trackPoint = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / duration);
      
      const easeProgress = progress < 0.5 
        ? 4 * progress * progress * progress 
        : 1 - Math.pow(-2 * progress + 2, 3) / 2;

      const point = this.strokePath.getPointAtLength(easeProgress * totalLength);
      const svgBox = this.strokePath.ownerSVGElement.getBoundingClientRect();
      const viewBox = this.strokePath.ownerSVGElement.viewBox.baseVal;

      const scaleX = svgBox.width / viewBox.width;
      const scaleY = svgBox.height / viewBox.height;

      const x = svgBox.left + point.x * scaleX;
      const y = svgBox.top + point.y * scaleY;

      this.penSparkle.style.left = `${x}px`;
      this.penSparkle.style.top = `${y}px`;

      if (progress < 1 && !this.isFinished) {
        requestAnimationFrame(trackPoint);
      } else {
        this.penSparkle.style.opacity = '0';
      }
    };

    requestAnimationFrame(trackPoint);
  }

  finishIntro() {
    if (this.isFinished) return;
    this.isFinished = true;

    if (this.animFrame) cancelAnimationFrame(this.animFrame);

    if (this.container) {
      this.container.style.opacity = '0';
      setTimeout(() => {
        // Directly transition to the dashboard
        window.location.href = '../dashboard/index.html';
      }, 500);
    } else {
      window.location.href = '../dashboard/index.html';
    }
  }

  skip() {
    this.finishIntro();
  }
}

/* ==========================================================================
   3. INTERACTIVE ACOUSTIC FREQUENCY LAB CANVAS
   ========================================================================== */
class WaveformLab {
  constructor() {
    this.canvas = document.getElementById('interactiveCanvas');
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.width = 0;
    this.height = 0;

    this.mouseX = 0;
    this.mouseY = 0;
    this.isHovering = false;
    this.isDragging = false;
    this.time = 0;
    this.animFrame = null;
    this.initialized = false;

    this.currentPreset = 'sine';
    this.presetConfigs = {
      sine: { name: 'SINE WAVE', harmonics: 4, speed: 0.05, amplitude: 25 },
      neural: { name: 'NEURAL HARMONIC', harmonics: 8, speed: 0.08, amplitude: 45 },
      harmonic: { name: 'PULSE ECHO', harmonics: 12, speed: 0.12, amplitude: 60 },
      spikes: { name: 'ACOUSTIC SPIKES', harmonics: 16, speed: 0.15, amplitude: 80 }
    };

    this.freqReadout = document.getElementById('freq-readout');
    this.harmonicsReadout = document.getElementById('harmonics-readout');
    this.particles = [];
  }

  init() {
    if (this.initialized) return;
    this.initialized = true;

    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.bindEvents();
    this.render();
  }

  resize() {
    if (!this.canvas || !this.canvas.parentElement) return;
    this.width = this.canvas.width = this.canvas.parentElement.clientWidth;
    this.height = this.canvas.height = this.canvas.parentElement.clientHeight;
    if (!this.isHovering) {
      this.mouseX = this.width / 2;
      this.mouseY = this.height / 2;
    }
  }

  bindEvents() {
    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouseX = e.clientX - rect.left;
      this.mouseY = e.clientY - rect.top;
      this.isHovering = true;
      this.updateReadouts();

      if (this.isDragging) {
        this.emitParticles(this.mouseX, this.mouseY, 2);
      }
    });

    this.canvas.addEventListener('mousedown', () => {
      this.isDragging = true;
      this.emitParticles(this.mouseX, this.mouseY, 8);
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
    });

    this.canvas.addEventListener('mouseleave', () => {
      this.isHovering = false;
    });
  }

  setPreset(presetKey) {
    if (this.presetConfigs[presetKey]) {
      this.currentPreset = presetKey;
      this.updateReadouts();
      if (audioEngine) audioEngine.playTone(600);
    }
  }

  updateReadouts() {
    const freqVal = Math.round(80 + (this.mouseX / (this.width || 1)) * 380);
    if (this.freqReadout) this.freqReadout.innerText = `${freqVal}.0 Hz`;
    if (this.harmonicsReadout) {
      this.harmonicsReadout.innerText = `${this.presetConfigs[this.currentPreset].harmonics} ACTIVE`;
    }
    if (audioEngine) audioEngine.setFrequency(freqVal);
  }

  emitParticles(x, y, count) {
    for (let i = 0; i < count; i++) {
      this.particles.push({
        x: x,
        y: y,
        vx: (Math.random() - 0.5) * 4,
        vy: (Math.random() - 0.5) * 4,
        size: Math.random() * 3 + 1,
        life: 1.0,
        decay: Math.random() * 0.03 + 0.02
      });
    }
  }

  render() {
    this.ctx.fillStyle = '#FAF6F0';
    this.ctx.fillRect(0, 0, this.width, this.height);

    const midY = this.height / 2;
    const totalBars = 100;
    const spacing = this.width / (totalBars + 1);
    const config = this.presetConfigs[this.currentPreset];

    this.ctx.lineWidth = 2.2;
    this.ctx.strokeStyle = '#3D261D';
    this.ctx.shadowColor = 'rgba(61, 38, 29, 0.2)';
    this.ctx.shadowBlur = 8;
    this.ctx.beginPath();

    for (let i = 0; i <= totalBars; i++) {
      const x = i * spacing;
      const distToMouse = Math.abs(x - this.mouseX);
      const mouseInfluence = Math.exp(-distToMouse * 0.012);

      const baseWave = Math.sin(i * 0.2 + this.time * config.speed) * config.amplitude;
      
      let harmonicWave = 0;
      for (let h = 1; h <= config.harmonics; h++) {
        harmonicWave += (Math.sin(i * 0.1 * h - this.time * config.speed * h) * 12) / h;
      }

      const userMod = Math.sin(i * 0.5 - this.time * 0.1) * (mouseInfluence * (this.isDragging ? 90 : 50));
      const amp = Math.max(2, Math.abs(baseWave + harmonicWave + userMod));

      this.ctx.moveTo(x, midY - amp);
      this.ctx.lineTo(x, midY + amp);

      if (distToMouse < spacing * 0.8) {
        this.ctx.fillStyle = '#3D261D';
        this.ctx.fillRect(x - 2, midY - amp - 4, 4, 4);
        this.ctx.fillRect(x - 2, midY + amp, 4, 4);
      }
    }
    this.ctx.stroke();
    this.ctx.shadowBlur = 0;

    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.life -= p.decay;

      if (p.life <= 0) {
        this.particles.splice(i, 1);
        continue;
      }

      this.ctx.fillStyle = `rgba(61, 38, 29, ${p.life * 0.6})`;
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      this.ctx.fill();
    }

    this.time += 1;
    this.animFrame = requestAnimationFrame(() => this.render());
  }
}

/* ==========================================================================
   4. UI CONTROLLER & BACKGROUND CONSTELLATION MESH
   ========================================================================== */
class UIController {
  constructor() {
    this.bgCanvas = document.getElementById('bg-particles-canvas');
    this.bgCtx = this.bgCanvas ? this.bgCanvas.getContext('2d') : null;
    this.particles = [];
    this.bgWidth = 0;
    this.bgHeight = 0;

    this.init();
  }

  init() {
    this.setupScrollObserver();
    this.setupCardEffects();
    this.initBackgroundParticles();
  }

  onIntroComplete() {
    this.setupScrollObserver();
  }

  setupScrollObserver() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
  }

  setupCardEffects() {
    document.querySelectorAll('.feature-card, .lab-section').forEach((card) => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        card.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
        card.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
      });
    });
  }

  initBackgroundParticles() {
    if (!this.bgCanvas || !this.bgCtx) return;

    const resizeBg = () => {
      this.bgWidth = this.bgCanvas.width = window.innerWidth;
      this.bgHeight = this.bgCanvas.height = window.innerHeight;
    };
    window.addEventListener('resize', resizeBg);
    resizeBg();

    const particleCount = 45;
    this.particles = [];

    for (let i = 0; i < particleCount; i++) {
      this.particles.push({
        x: Math.random() * this.bgWidth,
        y: Math.random() * this.bgHeight,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: Math.random() * 1.5 + 0.5,
        alpha: Math.random() * 0.4 + 0.1
      });
    }

    const renderBg = () => {
      this.bgCtx.clearRect(0, 0, this.bgWidth, this.bgHeight);

      for (let i = 0; i < this.particles.length; i++) {
        const p1 = this.particles[i];
        p1.x += p1.vx;
        p1.y += p1.vy;

        if (p1.x < 0) p1.x = this.bgWidth;
        if (p1.x > this.bgWidth) p1.x = 0;
        if (p1.y < 0) p1.y = this.bgHeight;
        if (p1.y > this.bgHeight) p1.y = 0;

        this.bgCtx.fillStyle = `rgba(61, 38, 29, ${p1.alpha * 0.4})`;
        this.bgCtx.beginPath();
        this.bgCtx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
        this.bgCtx.fill();

        for (let j = i + 1; j < this.particles.length; j++) {
          const p2 = this.particles[j];
          const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
          if (dist < 130) {
            const lineAlpha = (1 - dist / 130) * 0.12;
            this.bgCtx.strokeStyle = `rgba(61, 38, 29, ${lineAlpha})`;
            this.bgCtx.lineWidth = 0.5;
            this.bgCtx.beginPath();
            this.bgCtx.moveTo(p1.x, p1.y);
            this.bgCtx.lineTo(p2.x, p2.y);
            this.bgCtx.stroke();
          }
        }
      }

      requestAnimationFrame(renderBg);
    };

    renderBg();
  }
}

/* ==========================================================================
   5. APPLICATION INITIALIZATION & EVENT BINDINGS
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {
  audioEngine = new AudioEngine();
  introController = new IntroController();
  waveformLab = new WaveformLab();
  uiController = new UIController();

  introController.start();
  bindEvents();
});

function bindEvents() {
  const audioBtn = document.getElementById('audio-toggle-btn');
  const audioStatusText = document.getElementById('audio-status-text');

  if (audioBtn) {
    audioBtn.addEventListener('click', () => {
      if (audioEngine) {
        audioEngine.toggle((isActive) => {
          if (isActive) {
            audioBtn.classList.add('active');
            if (audioStatusText) audioStatusText.innerText = "AUDIO FX: ON";
          } else {
            audioBtn.classList.remove('active');
            if (audioStatusText) audioStatusText.innerText = "AUDIO FX: OFF";
          }
        });
      }
    });
  }

  const presetBtns = document.querySelectorAll('.preset-btn');
  presetBtns.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      presetBtns.forEach((b) => b.classList.remove('active'));
      e.target.classList.add('active');

      const presetKey = e.target.getAttribute('data-preset');
      if (waveformLab) waveformLab.setPreset(presetKey);
    });
  });
}

function skipToLandingPage() {
  if (introController) introController.skip();
}

function replayFullVideoAnimation() {
  window.scrollTo({ top: 0, behavior: 'smooth' });

  const landingPage = document.getElementById('landing-page');
  if (landingPage) landingPage.style.opacity = '0';

  if (introController) introController.start();
}
