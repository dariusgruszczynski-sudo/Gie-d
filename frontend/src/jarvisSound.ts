/** Original, synthesized arena-rock-style riff (Web Audio oscillators +
 * waveshaper distortion) -- NOT a reproduction of any copyrighted
 * recording. Paired with the browser's built-in speech synthesis for the
 * "voice" line, so nothing here depends on any external/licensed audio
 * file. */
export function playBootRiff(): void {
  try {
    const AudioContextCls = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new AudioContextCls();
    const now = ctx.currentTime;

    const curve = new Float32Array(44100);
    const amount = 30;
    for (let i = 0; i < 44100; i++) {
      const x = (i * 2) / 44100 - 1;
      curve[i] = ((Math.PI + amount) * x) / (Math.PI + amount * Math.abs(x));
    }
    const distortion = ctx.createWaveShaper();
    distortion.curve = curve;
    distortion.oversample = "4x";

    const masterGain = ctx.createGain();
    masterGain.gain.value = 0.1;
    distortion.connect(masterGain).connect(ctx.destination);

    function powerChord(freq: number, start: number, duration: number) {
      [freq, freq * 1.5, freq * 2].forEach((f) => {
        const osc = ctx.createOscillator();
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(f, now + start);
        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0, now + start);
        gain.gain.linearRampToValueAtTime(1, now + start + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, now + start + duration);
        osc.connect(gain).connect(distortion);
        osc.start(now + start);
        osc.stop(now + start + duration + 0.05);
      });
    }

    const riff = [
      { f: 82.41, t: 0, d: 0.28 }, // E2
      { f: 82.41, t: 0.3, d: 0.14 },
      { f: 98.0, t: 0.46, d: 0.14 }, // G2
      { f: 110.0, t: 0.62, d: 0.28 }, // A2
      { f: 82.41, t: 0.95, d: 0.28 },
      { f: 82.41, t: 1.25, d: 0.14 },
      { f: 98.0, t: 1.41, d: 0.14 },
      { f: 87.31, t: 1.57, d: 0.42 }, // F2
      { f: 82.41, t: 2.05, d: 0.5 },
    ];
    riff.forEach(({ f, t, d }) => powerChord(f, t, d));

    setTimeout(() => ctx.close(), 3000);
  } catch {
    // Web Audio unavailable/blocked -- boot animation still plays visually.
  }
}

export function speakBootLine(text: string): void {
  try {
    if (!("speechSynthesis" in window)) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "pl-PL";
    utterance.pitch = 0.7;
    utterance.rate = 0.95;
    const voices = window.speechSynthesis.getVoices();
    const plVoice = voices.find((v) => v.lang?.toLowerCase().startsWith("pl"));
    if (plVoice) utterance.voice = plVoice;
    window.speechSynthesis.speak(utterance);
  } catch {
    // Speech synthesis unavailable -- boot animation still plays visually.
  }
}
