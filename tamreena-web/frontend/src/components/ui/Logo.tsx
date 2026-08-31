interface LogoProps {
  size?: number;
}

/**
 * Wordmark badge: rounded-square lettermark with an accent dot.
 * Replaces the old neon-robot illustration — vector, theme-aware, no raster asset.
 */
function Logo({ size = 42 }: LogoProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 42 42" role="img" aria-label="Tamrena logo">
      <rect x="1" y="1" width="40" height="40" rx="12" fill="var(--text-heading)" />
      <text
        x="21"
        y="28"
        textAnchor="middle"
        fontFamily="'Newsreader', serif"
        fontWeight="700"
        fontSize="20"
        fill="var(--bg-page)"
      >
        T
      </text>
      <circle cx="33.5" cy="8.5" r="5" fill="var(--accent-primary)" stroke="var(--bg-page)" strokeWidth="2" />
    </svg>
  );
}

export default Logo;
