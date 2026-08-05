import { X, CheckCircle, WarningCircle, Info } from '@phosphor-icons/react'

const VARIANT_STYLES = {
  success: { border: 'border-ledger/30', Icon: CheckCircle, iconColor: 'text-ledger' },
  error: { border: 'border-crimson/30', Icon: WarningCircle, iconColor: 'text-crimson' },
  info: { border: 'border-mist-dim', Icon: Info, iconColor: 'text-ink-soft' },
}

export default function ToastViewport({ toasts, onDismiss }) {
  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-5 right-5 z-50 flex w-80 flex-col gap-2">
      {toasts.map((toast) => {
        const { border, Icon, iconColor } = VARIANT_STYLES[toast.variant] ?? VARIANT_STYLES.info
        return (
          <div
            key={toast.id}
            className={`flex items-start gap-2.5 rounded-card border ${border} bg-paper px-3.5 py-3 text-sm text-ink shadow-lg`}
          >
            <Icon size={18} className={`mt-0.5 shrink-0 ${iconColor}`} />
            <p className="flex-1">{toast.message}</p>
            <button
              onClick={() => onDismiss(toast.id)}
              className="text-ink-soft hover:text-ink"
              aria-label="Dismiss notification"
            >
              <X size={15} />
            </button>
          </div>
        )
      })}
    </div>
  )
}