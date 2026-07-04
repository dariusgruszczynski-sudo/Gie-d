export function BudgetGauge({ pctUsed, alert }: { pctUsed: number; alert: boolean }) {
  const clamped = Math.max(0, Math.min(100, pctUsed));
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped / 100);
  const color = alert ? "var(--red)" : clamped > 60 ? "var(--gold-bright)" : "var(--green)";

  return (
    <svg width="48" height="48" viewBox="0 0 48 48" className="budget-gauge" aria-hidden="true">
      <circle cx="24" cy="24" r={radius} fill="none" stroke="var(--border)" strokeWidth="5" />
      <circle
        cx="24"
        cy="24"
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth="5"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform="rotate(-90 24 24)"
      />
      <text x="24" y="27" textAnchor="middle" fontSize="11" fontWeight="700" fill="var(--text)">
        {Math.round(clamped)}%
      </text>
    </svg>
  );
}
