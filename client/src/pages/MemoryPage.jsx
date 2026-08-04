import { Plus } from '@phosphor-icons/react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

const MEMORIES = [
  { id: 1, content: 'User is vegetarian', updated: '5d ago' },
  { id: 2, content: 'User prefers concise answers over long explanations', updated: '2d ago' },
]

export default function MemoryPage() {
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <p className="text-sm text-ink-soft">2 remembered facts · placeholder data, CRUD wired up later</p>
        <Button>
          <Plus size={16} />
          Add fact
        </Button>
      </div>

      <div className="space-y-3">
        {MEMORIES.map((mem) => (
          <Card key={mem.id} tab="crimson" className="flex items-center justify-between">
            <p className="text-sm text-ink">{mem.content}</p>
            <p className="shrink-0 font-mono text-[11px] text-ink-soft">{mem.updated}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}