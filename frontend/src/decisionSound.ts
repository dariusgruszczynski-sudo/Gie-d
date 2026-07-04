type Action = "BUY" | "SELL" | "HOLD";

/** Synthesized via Web Audio API -- no external audio files, so it can never
 * 404 or depend on a CDN being reachable. Fails silently if audio is blocked
 * (e.g. no user interaction yet) -- the splash still shows visually. */
export function playDecisionSound(action: Action) {
  try {
    const AudioContextCls = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new AudioContextCls();
    const now = ctx.currentTime;

    function tone(freq: number, start: number, duration: number, type: OscillatorType, gainPeak: number) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, now + start);
      gain.gain.setValueAtTime(0, now + start);
      gain.gain.linearRampToValueAtTime(gainPeak, now + start + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + start + duration);
      osc.connect(gain).connect(ctx.destination);
      osc.start(now + start);
      osc.stop(now + start + duration + 0.05);
    }

    if (action === "BUY") {
      tone(523.25, 0, 0.16, "triangle", 0.16); // C5
      tone(659.25, 0.09, 0.16, "triangle", 0.16); // E5
      tone(783.99, 0.18, 0.32, "triangle", 0.18); // G5
    } else if (action === "SELL") {
      tone(587.33, 0, 0.16, "sawtooth", 0.11); // D5
      tone(440.0, 0.1, 0.16, "sawtooth", 0.11); // A4
      tone(329.63, 0.2, 0.34, "sawtooth", 0.12); // E4
    } else {
      tone(392.0, 0, 0.22, "sine", 0.13); // G4
      tone(392.0, 0.3, 0.32, "sine", 0.13); // G4
    }

    setTimeout(() => ctx.close(), 1500);
  } catch {
    // Web Audio unavailable or blocked -- fine, splash still shows.
  }
}
