import { useCallback, useState } from 'react'
import { NotePencil, PencilSimple, Trash, Plus } from '@phosphor-icons/react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import Alert from '../components/ui/Alert'
import EmptyState from '../components/ui/EmptyState'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import Drawer from '../components/ui/Drawer'
import IndexButton from '../components/ui/IndexButton'
import NoteForm from '../components/notes/NoteForm'
import { useResourceList } from '../hooks/useResourceList'
import { useToast } from '../lib/ToastContext'
import { getErrorMessage } from '../lib/errors'
import { fetchNotes, createNote, updateNote, deleteNote } from '../services/notesService'
import { triggerNoteIndex, fetchNoteIndexStatus } from '../services/retrievalService'

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function NotesPage() {
  const { items: notes, setItems: setNotes, loading, error, reload } = useResourceList(
    useCallback(() => fetchNotes(), [])
  )
  const { notify } = useToast()

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingNote, setEditingNote] = useState(null) // null = create, object = edit
  const [toDelete, setToDelete] = useState(null)
  const [deleting, setDeleting] = useState(false)

  function openCreate() {
    setEditingNote(null)
    setDrawerOpen(true)
  }

  function openEdit(note) {
    setEditingNote(note)
    setDrawerOpen(true)
  }

  async function handleSave({ title, content }) {
    if (editingNote) {
      const updated = await updateNote(editingNote.id, { title, content })
      setNotes((prev) => prev.map((n) => (n.id === updated.id ? updated : n)))
      notify('Note saved.', { variant: 'success' })
    } else {
      const created = await createNote({ title, content })
      setNotes((prev) => [created, ...prev])
      notify('Note created.', { variant: 'success' })
    }
    setDrawerOpen(false)
  }

  async function handleDelete() {
    if (!toDelete) return
    setDeleting(true)
    try {
      await deleteNote(toDelete.id)
      setNotes((prev) => prev.filter((n) => n.id !== toDelete.id))
      notify(`"${toDelete.title || 'Note'}" deleted.`, { variant: 'success' })
      setToDelete(null)
    } catch (err) {
      notify(getErrorMessage(err), { variant: 'error' })
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-ink-soft">
          {loading ? 'Loading…' : `${notes.length} note${notes.length !== 1 ? 's' : ''}`}
        </p>
        <Button onClick={openCreate}>
          <Plus size={16} /> New note
        </Button>
      </div>

      {error && !loading && (
        <Alert variant="error" className="mb-4">
          Could not load notes. <button onClick={reload} className="underline">Retry</button>
        </Alert>
      )}

      {loading && (
        <div className="flex justify-center py-16">
          <Spinner size={28} className="text-ink-soft" />
        </div>
      )}

      {!loading && !error && notes.length === 0 && (
        <EmptyState
          icon={<NotePencil size={40} />}
          title="No notes yet"
          hint="Notes are automatically indexed so the assistant can search them."
          action={<Button onClick={openCreate}><Plus size={16} /> New note</Button>}
        />
      )}

      {!loading && notes.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {notes.map((note) => (
            <Card key={note.id} tab="ledger" className="group">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-ink">
                    {note.title || <span className="italic text-ink-soft">Untitled</span>}
                  </p>
                  <p className="mt-1 line-clamp-2 text-sm text-ink-soft">{note.content}</p>
                  <div className="mt-2 flex items-center gap-3">
                    <span className="font-mono text-[11px] text-ink-soft">
                      {formatDate(note.updated_at)}
                    </span>
                    <IndexButton
                      onTrigger={() => triggerNoteIndex(note.id)}
                      onPoll={() => fetchNoteIndexStatus(note.id)}
                      initialStatus={null}
                    />
                  </div>
                </div>
                <div className="flex shrink-0 gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                  <button
                    onClick={() => openEdit(note)}
                    className="rounded-tab p-1.5 text-ink-soft hover:text-ink"
                    title="Edit"
                  >
                    <PencilSimple size={16} />
                  </button>
                  <button
                    onClick={() => setToDelete(note)}
                    className="rounded-tab p-1.5 text-ink-soft hover:text-crimson"
                    title="Delete"
                  >
                    <Trash size={16} />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Drawer
        title={editingNote ? 'Edit note' : 'New note'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <NoteForm
          note={editingNote}
          onSave={handleSave}
          onCancel={() => setDrawerOpen(false)}
        />
      </Drawer>

      {toDelete && (
        <ConfirmDialog
          title="Delete note"
          message={`"${toDelete.title || 'This note'}" will be permanently deleted.`}
          onConfirm={handleDelete}
          onCancel={() => setToDelete(null)}
          busy={deleting}
        />
      )}
    </div>
  )
}