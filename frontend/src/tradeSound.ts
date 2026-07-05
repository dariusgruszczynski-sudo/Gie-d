const MUTE_KEY = "gield_sound_muted";

export function isSoundMuted(): boolean {
  return localStorage.getItem(MUTE_KEY) === "1";
}

export function setSoundMuted(muted: boolean): void {
  localStorage.setItem(MUTE_KEY, muted ? "1" : "0");
}

/** A short, satisfying "cha-ching" played the moment a real trade executes.
 * Synthesized via the Web Audio API -- no audio files, so it can never 404 or
 * depend on a CDN. Plays even when the tab is in the background (once the audio
 * context was unlocked by the login click). Fails silently if audio is blocked
 * or muted. */
export function playTradeSound(side: "BUY" | "SELL"): void {
  if (isSoundMuted()) return;
  try {
    const AudioContextCls =
      window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new AudioContextCls();
    const now = ctx.currentTime;

    function tone(freq: number, start: number, duration: number, type: OscillatorType, gainPeak: number) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, now + start);
      gain.gain.setValueAtTime(0, now + start);
      gain.gain.linearRampToValueAtTime(gainPeak, now + start + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + start + duration);
      osc.connect(gain).connect(ctx.destination);
      osc.start(now + start);
      osc.stop(now + start + duration + 0.05);
    }

    if (side === "BUY") {
      // Bright ascending chime -- "entered a position".
      tone(659.25, 0, 0.12, "square", 0.13); // E5
      tone(987.77, 0.08, 0.3, "square", 0.15); // B5
      tone(1318.51, 0.15, 0.42, "triangle", 0.11); // E6
    } else {
      // Cash-register "ka-ching" -- "realized a result".
      tone(783.99, 0, 0.11, "square", 0.13); // G5
      tone(1046.5, 0.07, 0.34, "square", 0.15); // C6
      tone(1567.98, 0.14, 0.4, "triangle", 0.1); // G6
    }

    setTimeout(() => ctx.close(), 1600);
  } catch {
    // Web Audio unavailable or blocked -- ignore.
  }
}
