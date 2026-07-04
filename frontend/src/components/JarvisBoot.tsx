import { useEffect, useState } from "react";
import { playBootRiff, speakBootLine } from "../jarvisSound";

const LINES = ["WERYFIKACJA TOŻSAMOŚCI...", "DOSTĘP PRZYZNANY", "GIE-D ONLINE"];
const TOTAL_DURATION_MS = 4000;

export function JarvisBoot({ onComplete }: { onComplete: () => void }) {
  const [visibleLines, setVisibleLines] = useState(0);

  useEffect(() => {
    playBootRiff();
    speakBootLine("Weryfikacja tożsamości. Dostęp przyznany. Gie-d online.");

    const stepMs = TOTAL_DURATION_MS / (LINES.length + 1);
    const lineTimers = LINES.map((_, i) => setTimeout(() => setVisibleLines(i + 1), stepMs * (i + 1)));
    const doneTimer = setTimeout(onComplete, TOTAL_DURATION_MS);

    return () => {
      lineTimers.forEach(clearTimeout);
      clearTimeout(doneTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="jarvis-boot">
      <div className="jarvis-rings">
        <div className="jarvis-ring jarvis-ring-1" />
        <div className="jarvis-ring jarvis-ring-2" />
        <div className="jarvis-ring jarvis-ring-3" />
      </div>
      <div className="jarvis-lines">
        {LINES.slice(0, visibleLines).map((line, i) => (
          <p key={i} className="jarvis-line">
            {line}
          </p>
        ))}
      </div>
    </div>
  );
}
