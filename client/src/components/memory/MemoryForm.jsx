import { useState } from 'react'
import Button from '../ui/Button'
import Alert from '../ui/Alert'
import Spinner from '../ui/Spinner'
import { getErrorMessage } from '../../lib/errors'

export default function MemoryForm({ memory, onSave, onCancel }) {
  const [content, setContent] = useState(memory?.content ?? '')
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const isEditing = Boolean(memory)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!content.trim()) {
      setError('Content cannot be empty.')
      return
    }
    setError(null)
    setSaving(true)
    try {
      await onSave({ content: content.trim() })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {error && <Alert variant="error">{error}</Alert>}

      <label className="block">
        <span className="mb-1.5 block text-sm font-medium text-ink">Fact</span>
        <textarea
          rows={5}
          placeholder="e.g. User prefers concise answers…"
          value={content}
          autoFocus
          onChange={(e) => setContent(e.target.value)}
          className="w-full rounded-tab border border-mist bg-paper px-3 py-2 text-sm text-ink placeholder:text-ink-soft focus:outline-none focus:ring-1 focus:ring-ledger"
        />
        <p className="mt-1.5 text-xs text-ink-soft">
          Facts here are visible to the assistant and can be searched via{' '}
          <span className="font-mono">search_my_knowledge</span>.
        </p>
      </label>

      <div className="flex justify-end gap-3">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
        <Button type="submit" disabled={saving}>
          {saving && <Spinner size={15} />}
          {saving ? 'Saving…' : isEditing ? 'Save changes' : 'Add fact'}
        </Button>
      </div>
    </form>
  )
}