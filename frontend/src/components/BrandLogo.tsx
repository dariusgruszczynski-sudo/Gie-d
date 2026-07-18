export function BrandLogo({ size = 48 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" className="logo-mark" aria-label="GielDarek" role="img">
      <defs>
        <linearGradient id="gdTile" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#0b1120" />
          <stop offset="100%" stopColor="#05080f" />
        </linearGradient>
        <linearGradient id="gdGem" x1="0.1" y1="0.1" x2="0.9" y2="0.95">
          <stop offset="0%" stopColor="#19e39a" />
          <stop offset="100%" stopColor="#ffae34" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="44" height="44" rx="13" fill="url(#gdTile)" />
      <rect x="2" y="2" width="44" height="44" rx="13" fill="none" stroke="#ffffff" strokeOpacity="0.08" strokeWidth="1" />
      {/* Gem: mint→amber gradient frame with a dark centre and a mint spark. */}
      <rect x="12" y="12" width="24" height="24" rx="7" fill="url(#gdGem)" />
      <rect x="16" y="16" width="16" height="16" rx="4.5" fill="#070b14" />
      <circle cx="24" cy="24" r="2.1" fill="#19e39a" />
    </svg>
  );
}
