// The one component that makes every page in the app feel like part of the
// same catalog system. The colored left-edge tab tells you at a glance what
// kind of thing you're looking at, the same way a library used color-coded
// catalog cards to sort documents, notes and memory-style annotations.
const TAB_COLORS = {
  brass: 'var(--color-brass)',   // documents
  ledger: 'var(--color-ledger)', // notes / chat
  crimson: 'var(--color-crimson)', // memory / destructive
}

export default function Card({ tab = 'ledger', children, className = '', as: Tag = 'div', ...rest }) {
  return (
    <Tag
      className={`relative overflow-hidden rounded-card border border-mist bg-paper pl-5 pr-4 py-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ledger focus-visible:ring-offset-1 ${className}`}
      {...rest}
    >
      <span
        aria-hidden="true"
        className="absolute left-0 top-0 h-full w-1.5"
        style={{ backgroundColor: TAB_COLORS[tab] || TAB_COLORS.ledger }}
      />
      {children}
    </Tag>
  )
}