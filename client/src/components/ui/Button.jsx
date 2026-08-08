const VARIANTS = {
  primary: 'bg-ledger text-paper hover:bg-ledger-dim',
  ghost: 'bg-transparent text-ink-soft border border-mist hover:border-mist-dim hover:text-ink',
  danger: 'bg-transparent text-crimson border border-crimson/40 hover:bg-crimson/5',
}

export default function Button({ variant = 'primary', className = '', children, ...rest }) {
  return (
    <button
      className={`inline-flex items-center gap-2 rounded-tab px-3.5 py-2 text-sm font-medium font-body transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ledger focus-visible:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed ${VARIANTS[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  )
}