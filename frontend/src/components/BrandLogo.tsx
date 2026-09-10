export function BrandLogo({ size = 48 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" className="logo-mark" aria-label="GielDarek" role="img">
      <defs>
        <linearGradient id="gdTile" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#17120d" />
          <stop offset="100%" stopColor="#0a0806" />
        </linearGradient>
        <linearGradient id="gdGem" x1="0.1" y1="0.1" x2="0.9" y2="0.95">
          <stop offset="0%" stopColor="#e6a970" />
          <stop offset="100%" stopColor="#9c5a28" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="44" height="44" rx="13" fill="url(#gdTile)" />
      <rect x="2" y="2" width="44" height="44" rx="13" fill="none" stroke="#c7ccd2" strokeOpacity="0.14" strokeWidth="1" />
      {/* Klejnot: gradient miedzi (jasna→głęboka) z ciemnym środkiem i srebrną iskrą. */}
      <rect x="12" y="12" width="24" height="24" rx="7" fill="url(#gdGem)" />
      <rect x="16" y="16" width="16" height="16" rx="4.5" fill="#0a0806" />
      <circle cx="24" cy="24" r="2.1" fill="#c7ccd2" />
    </svg>
  );
}
