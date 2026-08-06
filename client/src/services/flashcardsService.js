import { useCallback, useState } from 'react'
import { Cards, Sparkle, Trash, CaretDown, CaretUp, PencilSimple, WarningCircle } from '@phosphor-icons/react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import Alert from '../components/ui/Alert'
import EmptyState from '../components/ui/EmptyState'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import Drawer from '../components/ui/Drawer'
import GenerateDialog from '../components/flashcards/GenerateDialog'
import FlipCard from '../components/flashcards/FlipCard'
import { useResourceList } from '../hooks/useResourceList'
import { usePolling } from '../hooks/usePolling'
import { useToast } from '../lib/ToastContext'
import { getErrorMessage } from '../lib/errors'
import {
  fetchFlashcardSets,
  fetchFlashcardSet,
  deleteFlashcardSet,
  updateFlashcard,
  deleteFlashcard,
} from '../services/flashcardsService'

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

// Polls a single pending set until it's no longer pending, then updates it in the list.
function PendingSetPoller({ setId, onDone, onError }) {
  const fetcher = useCallback(() => fetchFlashcardSet(setId), [setId])
  const stopWhen = useCallback((data) => data.status !== 'pending', [])
  usePolling({ fetcher, stopWhen, onDone, onError, enabled: true, intervalMs: 2500 })
  return null
}

// Inline card editor shown inside the study drawer.
function CardEditor({ card, onSave, onDelete }) {
  const [editing, setEditing] = useState(false)
  const [question, setQuestion] = useState(card.question)
  const [answer, setAnswer] = useState(card.answer)
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  async function handleSave() {
    setSaving(true)
    try {
      await onSave(card.id, { question, answer, difficulty: card.difficulty, category: card.category })
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  if (confirmDelete) {
    return (
      <ConfirmDialog
        title="Delete card"
        message="This card will be permanently removed from the set."
        onConfirm={() => onDelete(card.id)}
        onCancel={() => setConfirmDelete(false)}
      />
    )
  }

  if (editing) {
    return (
      <div className="rounded-card border border-mist p-4 space-y-3">
        <label className="block">
          <span className="mb-1 block text-xs font-medium text-ink-soft">Question</span>
          <textarea rows={3} value={question} onChange={(e) => setQuestion(e.target.value)}
            className="w-full rounded-tab border border-mist bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-ledger" />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs font-medium text-ink-soft">Answer</span>
          <textarea rows={3} value={answer} onChange={(e) => setAnswer(e.target.value)}
            className="w-full rounded-tab border border-mist bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-ledger" />
        </label>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setEditing(false)} disabled={saving}>Cancel</Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving && <Spinner size={14} />} Save
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="group relative">
      <FlipCard card={card} />
      <div className="absolute right-3 top-3 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <button onClick={() => setEditing(true)}
          className="rounded-tab bg-paper p-1.5 text-ink-soft shadow hover:text-ink" title="Edit">
          <PencilSimple size={14} />
        </button>
        <button onClick={() => setConfirmDelete(true)}
          className="rounded-tab bg-paper p-1.5 text-ink-soft shadow hover:text-crimson" title="Delete">
          <Trash size={14} />
        </button>
      </div>
    </div>
  )
}

export default function FlashcardsPage() {
  const { items: sets, setItems: setSets, loading, error, reload } = useResourceList(
    useCallback(() => fetchFlashcardSets(), [])
  )
  const { notify } = useToast()

  const [showGenerate, setShowGenerate] = useState(false)
  const [studySet, setStudySet] = useState(null)   // set being studied in the drawer
  const [studyCards, setStudyCards] = useState([]) // full cards for the open set
  const [loadingCards, setLoadingCards] = useState(false)
  const [toDeleteSet, setToDeleteSet] = useState(null)
  const [deletingSet, setDeletingSet] = useState(false)

  // When a new set is generated, add it to the list as pending and start polling.
  function handleGenerated(pendingSet) {
    setSets((prev) => [pendingSet, ...prev])
    setShowGenerate(false)
    notify('Generating flashcards… this takes a moment.', { variant: 'info' })
  }

  function handlePollDone(updatedSet) {
    setSets((prev) => prev.map((s) => (s.id === updatedSet.id ? updatedSet : s)))
    if (updatedSet.status === 'completed') {
      notify(`Flashcard set ready: ${updatedSet.source_title}`, { variant: 'success' })
    } else {
      notify(`Flashcard generation failed for "${updatedSet.source_title}".`, { variant: 'error' })
    }
  }

  function handlePollError(err) {
    notify(getErrorMessage(err), { variant: 'error' })
  }

  async function openStudy(set) {
    setLoadingCards(true)
    setStudySet(set)
    try {
      const full = await fetchFlashcardSet(set.id)
      setStudyCards(full.flashcards ?? [])
    } catch (err) {
      notify(getErrorMessage(err), { variant: 'error' })
      setStudySet(null)
    } finally {
      setLoadingCards(false)
    }
  }

  async function handleDeleteSet() {
    if (!toDeleteSet) return
    setDeletingSet(true)
    try {
      await deleteFlashcardSet(toDeleteSet.id)
      setSets((prev) => prev.filter((s) => s.id !== toDeleteSet.id))
      if (studySet?.id === toDeleteSet.id) setStudySet(null)
      notify('Flashcard set deleted.', { variant: 'success' })
      setToDeleteSet(null)
    } catch (err) {
      notify(getErrorMessage(err), { variant: 'error' })
    } finally {
      setDeletingSet(false)
    }
  }

  async function handleSaveCard(cardId, fields) {
    const updated = await updateFlashcard(cardId, fields)
    setStudyCards((prev) => prev.map((c) => (c.id === cardId ? updated : c)))
    notify('Card saved.', { variant: 'success' })
  }

  async function handleDeleteCard(cardId) {
    await deleteFlashcard(cardId)
    setStudyCards((prev) => prev.filter((c) => c.id !== cardId))
    notify('Card deleted.', { variant: 'success' })
  }

  const pendingSets = sets.filter((s) => s.status === 'pending')

  return (
    <div>
      {/* Render a hidden poller for each pending set */}
      {pendingSets.map((s) => (
        <PendingSetPoller
          key={s.id}
          setId={s.id}
          onDone={handlePollDone}
          onError={handlePollError}
        />
      ))}

      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-ink-soft">
          {loading ? 'Loading…' : `${sets.length} set${sets.length !== 1 ? 's' : ''}`}
        </p>
        <Button onClick={() => setShowGenerate(true)}>
          <Sparkle size={16} /> Generate set
        </Button>
      </div>

      {error && !loading && (
        <Alert variant="error" className="mb-4">
          Could not load flashcard sets. <button onClick={reload} className="underline">Retry</button>
        </Alert>
      )}

      {loading && (
        <div className="flex justify-center py-16">
          <Spinner size={28} className="text-ink-soft" />
        </div>
      )}

      {!loading && !error && sets.length === 0 && (
        <EmptyState
          icon={<Cards size={40} />}
          title="No flashcard sets yet"
          hint="Generate a set from any document or note to start studying."
          action={<Button onClick={() => setShowGenerate(true)}><Sparkle size={16} /> Generate set</Button>}
        />
      )}

      {!loading && sets.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {sets.map((set) => (
            <Card key={set.id} tab="brass" className="group">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-ink">{set.source_title}</p>
                  <p className="mt-1 font-mono text-[11px] text-ink-soft">
                    {set.status === 'pending' && (
                      <span className="flex items-center gap-1"><Spinner size={11} /> generating…</span>
                    )}
                    {set.status === 'completed' && `${set.flashcards?.length ?? '?'} cards · ${formatDate(set.created_at)}`}
                    {set.status === 'failed' && (
                      <span className="flex items-center gap-1 text-crimson"><WarningCircle size={12} weight="fill" /> failed</span>
                    )}
                  </p>
                </div>
                <div className="flex shrink-0 gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                  {set.status === 'completed' && (
                    <button onClick={() => openStudy(set)}
                      className="rounded-tab p-1.5 text-ink-soft hover:text-ink" title="Study">
                      <Cards size={16} />
                    </button>
                  )}
                  <button onClick={() => setToDeleteSet(set)}
                    className="rounded-tab p-1.5 text-ink-soft hover:text-crimson" title="Delete set">
                    <Trash size={16} />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Study drawer */}
      <Drawer
        title={studySet ? `${studySet.source_title}` : ''}
        open={Boolean(studySet)}
        onClose={() => setStudySet(null)}
      >
        {loadingCards && <div className="flex justify-center py-8"><Spinner size={24} className="text-ink-soft" /></div>}
        {!loadingCards && studyCards.length === 0 && (
          <p className="text-sm text-ink-soft">No cards in this set.</p>
        )}
        {!loadingCards && studyCards.length > 0 && (
          <div className="space-y-4">
            <p className="font-mono text-[11px] text-ink-soft">{studyCards.length} cards — click any card to flip</p>
            {studyCards.map((card) => (
              <CardEditor
                key={card.id}
                card={card}
                onSave={handleSaveCard}
                onDelete={handleDeleteCard}
              />
            ))}
          </div>
        )}
      </Drawer>

      {showGenerate && (
        <GenerateDialog
          onGenerated={handleGenerated}
          onCancel={() => setShowGenerate(false)}
        />
      )}

      {toDeleteSet && (
        <ConfirmDialog
          title="Delete flashcard set"
          message={`"${toDeleteSet.source_title}" and all its cards will be permanently deleted.`}
          onConfirm={handleDeleteSet}
          onCancel={() => setToDeleteSet(null)}
          busy={deletingSet}
        />
      )}
    </div>
  )
}