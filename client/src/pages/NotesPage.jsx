import { Plus } from '@phosphor-icons/react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

const NOTES = [
  { id: 1, title: 'Budget notes', content: 'We discussed cutting travel spend by 15% next quarter…', updated: '3d ago' },
  { id: 2, title: 'Reading list', content: 'Atomic Habits, Deep Work, The Pragmatic Programmer…', updated: '1w ago' },
]

export default function NotesPage() {
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <p className="text-sm text-ink-soft">2 notes · placeholder data, CRUD wired up later</p>
        <Button>
          <Plus size={16} />
          New note
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {NOTES.map((note) => (
          <Card key={note.id} tab="ledger">
            <p className="text-sm font-medium text-ink">{note.title}</p>
            <p className="mt-2 line-clamp-2 text-sm text-ink-soft">{note.content}</p>
            <p className="mt-3 font-mono text-[11px] text-ink-soft">updated {note.updated}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}