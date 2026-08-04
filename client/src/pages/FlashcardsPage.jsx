import { Cards, Sparkle } from '@phosphor-icons/react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

const SETS = [
  { id: 1, source: 'budget_report.txt', count: 10, status: 'completed' },
  { id: 2, source: 'Reading list', count: 6, status: 'completed' },
]

export default function FlashcardsPage() {
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <p className="text-sm text-ink-soft">2 sets · placeholder data, generation wired up later</p>
        <Button>
          <Sparkle size={16} />
          Generate set
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {SETS.map((set) => (
          <Card key={set.id} tab="brass">
            <div className="flex items-start gap-3">
              <Cards size={22} weight="duotone" className="mt-0.5 text-brass" />
              <div>
                <p className="text-sm font-medium text-ink">{set.source}</p>
                <p className="mt-1 font-mono text-[11px] text-ink-soft">
                  {set.count} cards · {set.status}
                </p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}