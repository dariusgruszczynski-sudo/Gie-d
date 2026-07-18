/** Living, video-like backdrop: a few big, heavily-blurred colour blobs that
 *  drift and breathe on long, offset loops — a slow aurora / lava-lamp motion
 *  behind the whole app. Pure CSS transforms (GPU-composited), so it stays
 *  smooth on a phone and costs nothing per frame in JS. Honours
 *  prefers-reduced-motion (the CSS pauses the drift). */
export function AuroraBackground() {
  return (
    <div className="aurora" aria-hidden="true">
      <span className="aurora-blob aurora-1" />
      <span className="aurora-blob aurora-2" />
      <span className="aurora-blob aurora-3" />
      <span className="aurora-blob aurora-4" />
      <div className="aurora-grain" />
      <div className="aurora-veil" />
    </div>
  );
}
