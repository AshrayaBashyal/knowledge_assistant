import { useState } from 'react'

const DIFFICULTY_COLORS = {
  easy: 'text-ledger',
  medium: 'text-brass',
  hard: 'text-crimson',
}

export default function FlipCard({ card }) {
  const [flipped, setFlipped] = useState(false)

  return (
    <button
      type="button"
      onClick={() => setFlipped((f) => !f)}
      className="group w-full rounded-card border border-mist bg-paper p-6 text-left transition-colors hover:border-mist-dim"
      aria-label={flipped ? 'Click to see question' : 'Click to reveal answer'}
    >
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
          {flipped ? 'Answer' : 'Question'}
        </span>
        <div className="flex items-center gap-3">
          {card.category && (
            <span className="font-mono text-[11px] text-ink-soft">{card.category}</span>
          )}
          {card.difficulty && (
            <span className={`font-mono text-[11px] capitalize ${DIFFICULTY_COLORS[card.difficulty] ?? 'text-ink-soft'}`}>
              {card.difficulty}
            </span>
          )}
        </div>
      </div>
      <p className="text-sm text-ink leading-relaxed">
        {flipped ? card.answer : card.question}
      </p>
      <p className="mt-4 text-[11px] text-ink-soft/60">
        {flipped ? 'Click to see question' : 'Click to reveal answer'}
      </p>
    </button>
  )
}