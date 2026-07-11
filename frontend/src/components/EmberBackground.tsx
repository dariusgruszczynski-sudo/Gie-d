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

const PARTICLE_COUNT = 55;
const ORB_COUNT = 5;

export function EmberBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
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

    // Large, slow, soft glow blobs -- distant parallax layer.
    const orbs: Orb[] = Array.from({ length: ORB_COUNT }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      r: 140 + Math.random() * 220,
      speed: 0.012 + Math.random() * 0.02,
      drift: (Math.random() - 0.5) * 0.03,
      opacity: 0.03 + Math.random() * 0.035,
    }));

    // Small, fast, bright embers -- foreground layer.
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
        const gradient = ctx!.createRadialGradient(o.x, o.y, 0, o.x, o.y, o.r);
        gradient.addColorStop(0, `rgba(56, 189, 248, ${o.opacity})`);
        gradient.addColorStop(1, "rgba(56, 189, 248, 0)");
        ctx!.fillStyle = gradient;
        ctx!.beginPath();
        ctx!.arc(o.x, o.y, o.r, 0, Math.PI * 2);
        ctx!.fill();
      }

      for (const e of embers) {
        const flicker = 0.7 + 0.3 * Math.sin(e.phase);
        const gradient = ctx!.createRadialGradient(e.x, e.y, 0, e.x, e.y, e.r * 5);
        gradient.addColorStop(0, `rgba(125, 211, 252, ${e.opacity * flicker})`);
        gradient.addColorStop(1, "rgba(125, 211, 252, 0)");
        ctx!.fillStyle = gradient;
        ctx!.beginPath();
        ctx!.arc(e.x, e.y, e.r * 5, 0, Math.PI * 2);
        ctx!.fill();
      }
    }

    let raf = 0;
    function step() {
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
      drawFrame();
      raf = requestAnimationFrame(step);
    }

    drawFrame();
    if (!reducedMotion) raf = requestAnimationFrame(step);

    return () => {
      window.removeEventListener("resize", resize);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return <canvas ref={canvasRef} className="ember-background" aria-hidden="true" />;
}
