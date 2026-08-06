import { useEffect, useState } from 'react'
import Button from '../ui/Button'
import Alert from '../ui/Alert'
import Spinner from '../ui/Spinner'
import { getErrorMessage } from '../../lib/errors'
import { fetchDocuments } from '../../services/documentsService'
import { fetchNotes } from '../../services/notesService'
import { generateFlashcards } from '../../services/flashcardsService'
import { MAX_FLASHCARDS_PER_SET } from '../../lib/env'

// Fetch documents and notes directly (not via useResourceList) so we have
// full control over when fetches fire and avoid the referential-instability
// problem that caused useResourceList's useEffect to loop on every render.
export default function GenerateDialog({ onGenerated, onCancel }) {
  const [documents, setDocuments] = useState([])
  const [notes, setNotes] = useState([])
  const [sourceType, setSourceType] = useState('document')
  const [sourceId, setSourceId] = useState('')
  const [count, setCount] = useState(10)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  // Fetch both lists once on mount - no dependency churn.
  useEffect(() => {
    fetchDocuments().then(setDocuments).catch(() => {})
    fetchNotes().then(setNotes).catch(() => {})
  }, [])

  // Reset the selected source when switching between documents and notes.
  useEffect(() => { setSourceId('') }, [sourceType])

  const sources = sourceType === 'document' ? documents : notes
  const sourceLabel = sourceType === 'document' ? 'original_filename' : 'title'

  async function handleSubmit(e) {
    e.preventDefault()
    if (!sourceId) {
      setError('Please select a source.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      const set = await generateFlashcards({ sourceType, sourceId: Number(sourceId), count })
      onGenerated(set)
    } catch (err) {
      setError(getErrorMessage(err))
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 px-4">
      <div className="w-full max-w-sm rounded-card border border-mist bg-paper p-6 shadow-xl">
        <h2 className="mb-4 font-display italic text-2xl text-ink">Generate flashcards</h2>

        {error && <Alert variant="error" className="mb-4">{error}</Alert>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-ink">Source type</span>
            <div className="flex gap-2">
              {['document', 'note'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setSourceType(type)}
                  className={`flex-1 rounded-tab border py-2 text-sm transition-colors ${
                    sourceType === type
                      ? 'border-ledger bg-ledger text-paper'
                      : 'border-mist text-ink-soft hover:text-ink'
                  }`}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
          </label>

          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-ink">
              {sourceType === 'document' ? 'Document' : 'Note'}
            </span>
            <select
              value={sourceId}
              onChange={(e) => setSourceId(e.target.value)}
              className="w-full rounded-tab border border-mist bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-ledger"
            >
              <option value="">Select a {sourceType}…</option>
              {sources.map((s) => (
                <option key={s.id} value={s.id}>{s[sourceLabel] || `#${s.id}`}</option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-ink">
              Number of cards{' '}
              <span className="font-normal text-ink-soft">(max {MAX_FLASHCARDS_PER_SET})</span>
            </span>
            <input
              type="number"
              min={1}
              max={MAX_FLASHCARDS_PER_SET}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="w-full rounded-tab border border-mist bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-ledger"
            />
          </label>

          <div className="flex justify-end gap-3 pt-1">
            <Button type="button" variant="ghost" onClick={onCancel} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting && <Spinner size={15} />}
              {submitting ? 'Starting…' : 'Generate'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}