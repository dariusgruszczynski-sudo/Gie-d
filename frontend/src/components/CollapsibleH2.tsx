/** A panel <h2> that doubles as a collapse toggle -- keeps long tables tidy
 *  (the user can fold what they're not looking at). Reuses the .thesis-toggle
 *  styling already used by the "Inwestuję w" card. */
export function CollapsibleH2({
  title,
  open,
  onToggle,
  summary,
}: {
  title: string;
  open: boolean;
  onToggle: () => void;
  summary?: string;
}) {
  return (
    <button type="button" className="thesis-toggle" onClick={onToggle} aria-expanded={open}>
      <h2 style={{ margin: 0 }}>{title}</h2>
      <span className="thesis-toggle-summary">
        {summary}
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          aria-hidden="true"
          style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s ease" }}
        >
          <path d="M2 4 L6 8 L10 4" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" />
        </svg>
      </span>
    </button>
  );
}
