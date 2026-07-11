export function BrandLogo({ size = 48 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" className="logo-mark" aria-label="GielDarek" role="img">
      <defs>
        <linearGradient id="gdBadge" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#7dd3fc" />
          <stop offset="55%" stopColor="#38bdf8" />
          <stop offset="100%" stopColor="#22d3ee" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="44" height="44" rx="13" fill="url(#gdBadge)" />
      <rect x="2" y="2" width="44" height="44" rx="13" fill="none" stroke="#ffffff" strokeOpacity="0.16" strokeWidth="1" />
      <polyline
        points="12,32 21,24 28,29 37,15"
        fill="none"
        stroke="#0a0c14"
        strokeWidth="3.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M37 15 h-6.5 M37 15 v6.5"
        fill="none"
        stroke="#0a0c14"
        strokeWidth="3.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
