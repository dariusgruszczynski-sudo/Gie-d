/** A consistent bold section header (eyebrow + title) used to structure the
 *  rebuilt pages -- turns a flat stack of panels into clear, scannable
 *  chapters. Optional right-side slot for a small action/label. */
export function SectionTitle({
  eyebrow,
  title,
  right,
}: {
  eyebrow: string;
  title: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="sec-title">
      <div className="sec-title-text">
        <span className="sec-title-eyebrow">{eyebrow}</span>
        <h2 className="sec-title-h">{title}</h2>
      </div>
      {right && <div className="sec-title-right">{right}</div>}
    </div>
  );
}
