import { useEffect, useState } from "react";
import { BrandLogo } from "./BrandLogo";

const HOLD_MS = 1700; // logo + progress fill
const FADE_MS = 500; // fade-out into the app

/** Elegant, silent brand loading transition shown right after login before the
 * dashboard mounts. No sound. */
export function BrandLoader({ onComplete }: { onComplete: () => void }) {
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const t1 = setTimeout(() => setLeaving(true), HOLD_MS);
    const t2 = setTimeout(onComplete, HOLD_MS + FADE_MS);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className={`brand-loader ${leaving ? "brand-loader-leaving" : ""}`}>
      <div className="brand-loader-glow" />
      <div className="brand-loader-mark">
        <BrandLogo size={76} />
      </div>
      <div className="brand-loader-word">
        Giel<span>Darek</span>
      </div>
      <div className="brand-loader-bar">
        <span />
      </div>
    </div>
  );
}
