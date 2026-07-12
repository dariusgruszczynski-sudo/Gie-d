import { useEffect, useRef } from "react";

interface Ember {
  x: number;
  y: number;
  r: number;
  speed: number;
  drift: number;
  phase: number;
  opacity: number;
}

interface Orb {
  x: number;
  y: number;
  r: number;
  speed: number;
  drift: number;
  opacity: number;
}

// Pre-render one soft radial glow to an offscreen sprite, then drawImage it per
// particle. createRadialGradient per particle per frame (the old approach) was
// the main CPU cost -- ~60 gradients/frame melted phones. The sprite is built
// once; the hot loop only blits + tweaks alpha.
function makeGlowSprite(rgb: string): HTMLCanvasElement {
  const size = 128;
  const c = document.createElement("canvas");
  c.width = size;
  c.height = size;
  const g = c.getContext("2d")!;
  const grad = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grad.addColorStop(0, `rgba(${rgb}, 1)`);
  grad.addColorStop(1, `rgba(${rgb}, 0)`);
  g.fillStyle = grad;
  g.fillRect(0, 0, size, size);
  return c;
}

export function EmberBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    // Lighter particle load on phones -- fewer draws, smoother scroll.
    const mobile = window.matchMedia("(max-width: 640px)").matches;
    const PARTICLE_COUNT = mobile ? 26 : 55;
    const ORB_COUNT = mobile ? 3 : 5;

    let width = window.innerWidth;
    let height = window.innerHeight;

    function resize() {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas!.width = width * dpr;
      canvas!.height = height * dpr;
      canvas!.style.width = `${width}px`;
      canvas!.style.height = `${height}px`;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener("resize", resize);

    const orbSprite = makeGlowSprite("56, 189, 248");
    const emberSprite = makeGlowSprite("125, 211, 252");

    const orbs: Orb[] = Array.from({ length: ORB_COUNT }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      r: 140 + Math.random() * 220,
      speed: 0.012 + Math.random() * 0.02,
      drift: (Math.random() - 0.5) * 0.03,
      opacity: 0.03 + Math.random() * 0.035,
    }));

    const embers: Ember[] = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      r: 0.6 + Math.random() * 1.7,
      speed: 0.1 + Math.random() * 0.25,
      drift: (Math.random() - 0.5) * 0.25,
      phase: Math.random() * Math.PI * 2,
      opacity: 0.12 + Math.random() * 0.3,
    }));

    function drawFrame() {
      ctx!.clearRect(0, 0, width, height);
      for (const o of orbs) {
        ctx!.globalAlpha = o.opacity;
        const d = o.r * 2;
        ctx!.drawImage(orbSprite, o.x - o.r, o.y - o.r, d, d);
      }
      for (const e of embers) {
        const flicker = 0.7 + 0.3 * Math.sin(e.phase);
        ctx!.globalAlpha = e.opacity * flicker;
        const rr = e.r * 5;
        const d = rr * 2;
        ctx!.drawImage(emberSprite, e.x - rr, e.y - rr, d, d);
      }
      ctx!.globalAlpha = 1;
    }

    function advance() {
      for (const o of orbs) {
        o.y -= o.speed;
        o.x += o.drift;
        if (o.y < -o.r) {
          o.y = height + o.r;
          o.x = Math.random() * width;
        }
        if (o.x < -o.r) o.x = width + o.r;
        if (o.x > width + o.r) o.x = -o.r;
      }
      for (const e of embers) {
        e.phase += 0.012;
        e.y -= e.speed;
        e.x += e.drift;
        if (e.y < -10) {
          e.y = height + 10;
          e.x = Math.random() * width;
        }
        if (e.x < -10) e.x = width + 10;
        if (e.x > width + 10) e.x = -10;
      }
    }

    // Cap to ~30fps: the motion is slow, so half the frames look identical but
    // cost half the CPU/battery -- a big win on phones.
    const frameInterval = 1000 / 30;
    let last = 0;
    let raf = 0;
    let paused = false;

    function loop(now: number) {
      raf = requestAnimationFrame(loop);
      if (now - last < frameInterval) return;
      last = now;
      advance();
      drawFrame();
    }

    // Stop animating entirely while the tab/app is hidden -- no point burning
    // battery on an off-screen canvas.
    function onVisibility() {
      if (document.hidden) {
        if (raf) cancelAnimationFrame(raf);
        raf = 0;
        paused = true;
      } else if (paused && !reducedMotion) {
        paused = false;
        last = 0;
        raf = requestAnimationFrame(loop);
      }
    }
    document.addEventListener("visibilitychange", onVisibility);

    drawFrame();
    if (!reducedMotion) raf = requestAnimationFrame(loop);

    return () => {
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVisibility);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return <canvas ref={canvasRef} className="ember-background" aria-hidden="true" />;
}
