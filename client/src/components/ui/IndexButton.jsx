import { useCallback, useState } from 'react'
import { ArrowsClockwise, CheckCircle, WarningCircle, Database } from '@phosphor-icons/react'
import Spinner from './Spinner'
import { usePolling } from '../../hooks/usePolling'
import { getErrorMessage } from '../../lib/errors'

const STATUS = {
  idle: 'idle',
  triggering: 'triggering',
  pending: 'pending',
  indexed: 'indexed',
  failed: 'failed',
}

// Trigger, poll, and show result - all in one button.
// `onTrigger` calls POST /retrieval/.../index/
// `onPoll`    calls GET  /retrieval/.../index/
// Both are passed in by the parent so this component stays source-agnostic
// (works for documents and notes).
export default function IndexButton({ onTrigger, onPoll, initialStatus }) {
  const [status, setStatus] = useState(initialStatus === 'indexed' ? STATUS.indexed : STATUS.idle)
  const [errorMsg, setErrorMsg] = useState(null)
  const [pollingEnabled, setPollingEnabled] = useState(false)

  const fetcher = useCallback(() => onPoll(), [onPoll])
  const stopWhen = useCallback((data) => data.status !== 'pending', [])
  const onDone = useCallback((data) => {
    if (data.status === 'indexed') {
      setStatus(STATUS.indexed)
    } else {
      setStatus(STATUS.failed)
      setErrorMsg(data.error || 'Indexing failed.')
    }
    setPollingEnabled(false)
  }, [])
  const onError = useCallback((err) => {
    setStatus(STATUS.failed)
    setErrorMsg(getErrorMessage(err))
    setPollingEnabled(false)
  }, [])

  const { polling } = usePolling({ fetcher, stopWhen, onDone, onError, enabled: pollingEnabled })

  async function handleClick() {
    if (status === STATUS.indexed || status === STATUS.triggering || polling) return
    setStatus(STATUS.triggering)
    setErrorMsg(null)
    try {
      await onTrigger()
      setStatus(STATUS.pending)
      setPollingEnabled(true)
    } catch (err) {
      setStatus(STATUS.failed)
      setErrorMsg(getErrorMessage(err))
    }
  }

  if (status === STATUS.indexed) {
    return (
      <span className="flex items-center gap-1 font-mono text-[11px] text-ledger">
        <CheckCircle size={13} weight="fill" /> indexed
      </span>
    )
  }

  if (status === STATUS.failed) {
    return (
      <button
        onClick={handleClick}
        title={errorMsg ?? 'Indexing failed — click to retry'}
        className="flex items-center gap-1 font-mono text-[11px] text-crimson hover:underline"
      >
        <WarningCircle size={13} weight="fill" /> failed · retry
      </button>
    )
  }

  if (status === STATUS.pending || polling) {
    return (
      <span className="flex items-center gap-1 font-mono text-[11px] text-ink-soft">
        <Spinner size={12} /> indexing…
      </span>
    )
  }

  return (
    <button
      onClick={handleClick}
      disabled={status === STATUS.triggering}
      className="flex items-center gap-1 font-mono text-[11px] text-ink-soft hover:text-ledger disabled:opacity-50"
      title="Index for AI search"
    >
      {status === STATUS.triggering ? <Spinner size={12} /> : <Database size={13} />}
      {status === STATUS.triggering ? 'starting…' : 'index'}
    </button>
  )
}