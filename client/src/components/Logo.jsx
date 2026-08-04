// Hand-built mark, not a stock icon or generated image. Two catalog cards
// fanned slightly apart, the back one showing a guide tab - a small nod to
// the card-catalog motif that runs through the rest of the app.
export default function Logo({ size = 28, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* back card, rotated, with a guide tab poking out the top */}
      <g transform="rotate(-8 16 16)">
        <rect x="9" y="5" width="16" height="21" rx="1" fill="var(--color-paper-dim)" stroke="var(--color-mist-dim)" strokeWidth="1" />
        <rect x="12" y="4" width="6" height="3" rx="0.5" fill="var(--color-brass)" />
      </g>
      {/* front card, straight, with two ruled lines like a catalog entry */}
      <g>
        <rect x="7" y="7" width="16" height="21" rx="1" fill="var(--color-paper)" stroke="var(--color-ledger)" strokeWidth="1.4" />
        <line x1="10" y1="14" x2="20" y2="14" stroke="var(--color-ledger)" strokeWidth="1.2" strokeLinecap="round" />
        <line x1="10" y1="18" x2="17" y2="18" stroke="var(--color-mist-dim)" strokeWidth="1.2" strokeLinecap="round" />
      </g>
    </svg>
  )
}