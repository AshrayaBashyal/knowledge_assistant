import { useEffect } from 'react'
import { X } from '@phosphor-icons/react'

// A right-side panel that slides in over the content. Chosen over a modal
// for create/edit forms because the user can still see the list behind it,
// which helps with context when editing.
export default function Drawer({ title, open, onClose, children }) {
  // Close on Escape key
  useEffect(() => {
    if (!open) return
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <>
      {/* backdrop */}
      <div
        className="fixed inset-0 z-40 bg-ink/20"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* panel */}
      <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-mist bg-paper shadow-xl">
        <div className="flex items-center justify-between border-b border-mist px-6 py-4">
          <h2 className="font-display italic text-2xl text-ink">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-tab p-1.5 text-ink-soft hover:text-ink"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {children}
        </div>
      </div>
    </>
  )
}