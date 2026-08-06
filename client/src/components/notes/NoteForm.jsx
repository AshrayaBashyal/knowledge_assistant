import { useState } from 'react'
import Button from '../ui/Button'
import Field from '../ui/Field'
import Alert from '../ui/Alert'
import Spinner from '../ui/Spinner'
import { getErrorMessage } from '../../lib/errors'

// Used for both creating and editing a note. When `note` is passed in,
// fields are pre-filled and the save call is an update; otherwise it's a
// create. The backend auto-indexes notes on save so there's no IndexButton
// here unlike documents.
export default function NoteForm({ note, onSave, onCancel }) {
  const [title, setTitle] = useState(note?.title ?? '')
  const [content, setContent] = useState(note?.content ?? '')
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const isEditing = Boolean(note)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!title.trim() && !content.trim()) {
      setError('A note needs at least a title or some content.')
      return
    }
    setError(null)
    setSaving(true)
    try {
      await onSave({ title: title.trim(), content: content.trim() })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {error && <Alert variant="error">{error}</Alert>}

      <Field
        label="Title"
        type="text"
        placeholder="Give it a name…"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />

      <label className="block">
        <span className="mb-1.5 block text-sm font-medium text-ink">Content</span>
        <textarea
          rows={10}
          placeholder="Write something…"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full rounded-tab border border-mist bg-paper px-3 py-2 text-sm text-ink placeholder:text-ink-soft focus:outline-none focus:ring-1 focus:ring-ledger"
        />
      </label>

      <div className="flex justify-end gap-3">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
        <Button type="submit" disabled={saving}>
          {saving ? <Spinner size={15} /> : null}
          {saving ? 'Saving…' : isEditing ? 'Save changes' : 'Create note'}
        </Button>
      </div>
    </form>
  )
}