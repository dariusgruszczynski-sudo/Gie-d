export function BrandLogo({ size = 48 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" className="logo-mark" aria-label="GielDarek" role="img">
      <defs>
        <linearGradient id="gdTile" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#121c2c" />
          <stop offset="100%" stopColor="#05080f" />
        </linearGradient>
        <linearGradient id="gdRing" x1="0.1" y1="0.1" x2="0.9" y2="0.95">
          <stop offset="0%" stopColor="#19e39a" />
          <stop offset="100%" stopColor="#ffae34" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="44" height="44" rx="13" fill="url(#gdTile)" />
      <rect x="2" y="2" width="44" height="44" rx="13" fill="none" stroke="#ffffff" strokeOpacity="0.1" strokeWidth="1" />
      {/* Allocation ring (violet -> gold), open at the bottom -- the brand motif. */}
      <path
        d="M 11.71 32.60 A 15 15 0 1 1 25.31 38.94"
        fill="none"
        stroke="url(#gdRing)"
        strokeWidth="4.4"
        strokeLinecap="round"
      />
      {/* Upward chart line + arrow inside. */}
      <polyline
        points="16.3,30.2 21.6,25.0 26.4,27.8 32.2,19.2"
        fill="none"
        stroke="#f5f6fc"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M32.2 19.2 h-4.1 M32.2 19.2 v4.1"
        fill="none"
        stroke="#f5f6fc"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
