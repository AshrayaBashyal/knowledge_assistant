import { useCallback, useState } from 'react'
import { Brain, PencilSimple, Trash, Plus } from '@phosphor-icons/react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import Alert from '../components/ui/Alert'
import EmptyState from '../components/ui/EmptyState'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import Drawer from '../components/ui/Drawer'
import MemoryForm from '../components/memory/MemoryForm'
import { useResourceList } from '../hooks/useResourceList'
import { useToast } from '../lib/ToastContext'
import { getErrorMessage } from '../lib/errors'
import { fetchMemories, createMemory, updateMemory, deleteMemory } from '../services/memoryService'

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function MemoryPage() {
  const { items: memories, setItems: setMemories, loading, error, reload } = useResourceList(
    useCallback(() => fetchMemories(), [])
  )
  const { notify } = useToast()

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingMemory, setEditingMemory] = useState(null)
  const [toDelete, setToDelete] = useState(null)
  const [deleting, setDeleting] = useState(false)

  function openCreate() {
    setEditingMemory(null)
    setDrawerOpen(true)
  }

  function openEdit(memory) {
    setEditingMemory(memory)
    setDrawerOpen(true)
  }

  async function handleSave({ content }) {
    if (editingMemory) {
      const updated = await updateMemory(editingMemory.id, { content })
      setMemories((prev) => prev.map((m) => (m.id === updated.id ? updated : m)))
      notify('Fact updated.', { variant: 'success' })
    } else {
      const created = await createMemory({ content })
      setMemories((prev) => [created, ...prev])
      notify('Fact added.', { variant: 'success' })
    }
    setDrawerOpen(false)
  }

  async function handleDelete() {
    if (!toDelete) return
    setDeleting(true)
    try {
      await deleteMemory(toDelete.id)
      setMemories((prev) => prev.filter((m) => m.id !== toDelete.id))
      notify('Fact deleted.', { variant: 'success' })
      setToDelete(null)
    } catch (err) {
      notify(getErrorMessage(err), { variant: 'error' })
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <p className="text-sm text-ink-soft">
          {loading ? 'Loading…' : `${memories.length} remembered fact${memories.length !== 1 ? 's' : ''}`}
        </p>
        <Button onClick={openCreate}>
          <Plus size={16} /> Add fact
        </Button>
      </div>

      {/* Context note - memory facts are written by the agent too, this
          page just makes them transparent and editable by the user. */}
      <p className="mb-5 text-xs text-ink-soft">
        Facts the assistant has remembered. You can add, edit or delete them here at any time.
      </p>

      {error && !loading && (
        <Alert variant="error" className="mb-4">
          Could not load memory. <button onClick={reload} className="underline">Retry</button>
        </Alert>
      )}

      {loading && (
        <div className="flex justify-center py-16">
          <Spinner size={28} className="text-ink-soft" />
        </div>
      )}

      {!loading && !error && memories.length === 0 && (
        <EmptyState
          icon={<Brain size={40} />}
          title="Nothing remembered yet"
          hint="The assistant writes facts here automatically when you share things worth keeping. You can also add them manually."
          action={<Button onClick={openCreate}><Plus size={16} /> Add fact</Button>}
        />
      )}

      {!loading && memories.length > 0 && (
        <div className="space-y-2">
          {memories.map((mem) => (
            <Card key={mem.id} tab="crimson" className="group flex items-start gap-4">
              <p className="min-w-0 flex-1 break-words text-sm text-ink">{mem.content}</p>
              <div className="flex shrink-0 flex-col items-end gap-2">
                <span className="font-mono text-[11px] text-ink-soft">{formatDate(mem.updated_at)}</span>
                <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                  <button
                    onClick={() => openEdit(mem)}
                    className="rounded-tab p-1.5 text-ink-soft hover:text-ink"
                    title="Edit"
                  >
                    <PencilSimple size={15} />
                  </button>
                  <button
                    onClick={() => setToDelete(mem)}
                    className="rounded-tab p-1.5 text-ink-soft hover:text-crimson"
                    title="Delete"
                  >
                    <Trash size={15} />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Drawer
        title={editingMemory ? 'Edit fact' : 'Add fact'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <MemoryForm
          memory={editingMemory}
          onSave={handleSave}
          onCancel={() => setDrawerOpen(false)}
        />
      </Drawer>

      {toDelete && (
        <ConfirmDialog
          title="Delete fact"
          message="This fact will be permanently removed from the assistant's memory."
          onConfirm={handleDelete}
          onCancel={() => setToDelete(null)}
          busy={deleting}
        />
      )}
    </div>
  )
}