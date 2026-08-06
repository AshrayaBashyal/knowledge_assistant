import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  MagnifyingGlass,
  FileText,
  NotePencil,
  ChatCircleDots,
  ArrowRight,
} from '@phosphor-icons/react'
import Card from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'
import Alert from '../components/ui/Alert'
import EmptyState from '../components/ui/EmptyState'
import { useDebounce } from '../hooks/useDebounce'
import { search } from '../services/searchService'
import { getErrorMessage } from '../lib/errors'

// Each result type maps to a card tab color and an icon, same as the rest
// of the app - documents are brass, notes and messages are ledger.
const TYPE_META = {
  document: { tab: 'brass', Icon: FileText, label: 'Document' },
  note: { tab: 'ledger', Icon: NotePencil, label: 'Note' },
  message: { tab: 'ledger', Icon: ChatCircleDots, label: 'Message' },
}

// Group results by type so they're easier to scan.
function groupResults(results) {
  const order = ['document', 'note', 'message']
  const groups = {}
  for (const r of results) {
    if (!groups[r.type]) groups[r.type] = []
    groups[r.type].push(r)
  }
  return order.filter((t) => groups[t]).map((t) => ({ type: t, items: groups[t] }))
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const debouncedQuery = useDebounce(query, 350)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searched, setSearched] = useState(false) // true once the first search fires
  const inputRef = useRef(null)
  const navigate = useNavigate()

  // Auto-focus the search input on mount.
  useEffect(() => { inputRef.current?.focus() }, [])

  useEffect(() => {
    if (!debouncedQuery.trim()) {
      setResults([])
      setSearched(false)
      setError(null)
      return
    }

    let cancelled = false
    async function run() {
      setLoading(true)
      setError(null)
      try {
        const data = await search(debouncedQuery)
        if (!cancelled) {
          setResults(data.results)
          setSearched(true)
        }
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [debouncedQuery])

  function handleResultClick(result) {
    if (result.type === 'document') navigate('/documents')
    else if (result.type === 'note') navigate('/notes')
    else if (result.type === 'message') navigate(`/chat/${result.conversation_id}`)
  }

  const groups = groupResults(results)
  const totalCount = results.length

  return (
    <div className="mx-auto max-w-2xl">
      {/* Search input */}
      <div className="relative mb-6">
        <MagnifyingGlass
          size={18}
          className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-soft"
        />
        {loading && (
          <Spinner
            size={16}
            className="absolute right-3.5 top-1/2 -translate-y-1/2 text-ink-soft"
          />
        )}
        <input
          ref={inputRef}
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search documents, notes, and conversations…"
          className="w-full rounded-tab border border-mist bg-paper py-3 pl-10 pr-10 text-sm text-ink placeholder:text-ink-soft focus:outline-none focus:ring-1 focus:ring-ledger"
        />
      </div>

      {error && <Alert variant="error" className="mb-4">{error}</Alert>}

      {/* Empty query state */}
      {!query.trim() && (
        <EmptyState
          icon={<MagnifyingGlass size={36} />}
          title="Search your workspace"
          hint="Searches across documents, notes, and conversation messages using full-text matching."
        />
      )}

      {/* No results */}
      {searched && !loading && !error && totalCount === 0 && (
        <EmptyState
          icon={<MagnifyingGlass size={36} />}
          title={`No results for "${debouncedQuery}"`}
          hint="Try different keywords. Note: this is keyword search, not the same semantic search the assistant uses."
        />
      )}

      {/* Results grouped by type */}
      {totalCount > 0 && (
        <div className="space-y-6">
          <p className="text-sm text-ink-soft">
            {totalCount} result{totalCount !== 1 ? 's' : ''} for{' '}
            <span className="font-medium text-ink">"{debouncedQuery}"</span>
          </p>

          {groups.map(({ type, items }) => {
            const { tab, Icon, label } = TYPE_META[type]
            return (
              <div key={type}>
                <p className="mb-2 font-mono text-[11px] uppercase tracking-widest text-ink-soft">
                  {label}s — {items.length}
                </p>
                <div className="space-y-2">
                  {items.map((result) => (
                    <Card
                      key={`${result.type}-${result.id}`}
                      tab={tab}
                      as="button"
                      onClick={() => handleResultClick(result)}
                      className="w-full text-left transition-colors hover:border-mist-dim"
                    >
                      <div className="flex items-start gap-3">
                        <Icon size={17} className="mt-0.5 shrink-0 text-ink-soft" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-ink">{result.title}</p>
                          {result.snippet && result.snippet !== result.title && (
                            <p className="mt-0.5 line-clamp-2 text-sm text-ink-soft">{result.snippet}</p>
                          )}
                        </div>
                        <ArrowRight size={15} className="mt-0.5 shrink-0 text-ink-soft/50" />
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}