import { WarningCircle, Info } from '@phosphor-icons/react'

const VARIANTS = {
  error: { border: 'border-crimson/30', bg: 'bg-crimson/5', text: 'text-crimson', Icon: WarningCircle },
  info: { border: 'border-mist-dim', bg: 'bg-paper-dim', text: 'text-ink-soft', Icon: Info },
}

export default function Alert({ variant = 'error', children, className = '' }) {
  const { border, bg, text, Icon } = VARIANTS[variant]
  return (
    <div className={`flex items-start gap-2.5 rounded-tab border ${border} ${bg} px-3.5 py-2.5 text-sm ${text} ${className}`}>
      <Icon size={17} className="mt-0.5 shrink-0" />
      <div>{children}</div>
    </div>
  )
}