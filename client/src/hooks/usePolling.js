import { useCallback, useEffect, useRef, useState } from 'react'

// Polls a fetcher on an interval until a stopWhen predicate returns true,
// or until maxAttempts is reached. Cleans up the interval automatically
// when the component unmounts or when polling resolves.
//
// Used by retrieval indexing and flashcard generation later
// - both follow the same "POST to start, GET to poll" backend pattern.
export function usePolling({
  fetcher,         // async () => data
  stopWhen,        // (data) => boolean - stop polling when true
  onDone,          // (data) => void - called when stopWhen first returns true
  onError,         // (err) => void - called if any poll throws
  intervalMs = 3000,
  maxAttempts = 20, // 3s * 20 = 2 min ceiling
  enabled = false,  // start polling only when set to true
}) {
  const [polling, setPolling] = useState(false)
  const attemptsRef = useRef(0)
  const onDoneRef = useRef(onDone)
  const onErrorRef = useRef(onError)
  const stopWhenRef = useRef(stopWhen)

  // Keep refs current so interval closure always calls the latest callbacks
  // without needing them as dependencies (which would restart the interval).
  useEffect(() => { onDoneRef.current = onDone }, [onDone])
  useEffect(() => { onErrorRef.current = onError }, [onError])
  useEffect(() => { stopWhenRef.current = stopWhen }, [stopWhen])

  const stop = useCallback(() => {
    setPolling(false)
    attemptsRef.current = 0
  }, [])

  useEffect(() => {
    if (!enabled) return

    setPolling(true)
    attemptsRef.current = 0

    const id = setInterval(async () => {
      attemptsRef.current += 1

      if (attemptsRef.current > maxAttempts) {
        clearInterval(id)
        stop()
        onErrorRef.current?.(new Error('Polling timed out after too many attempts.'))
        return
      }

      try {
        const data = await fetcher()
        if (stopWhenRef.current(data)) {
          clearInterval(id)
          stop()
          onDoneRef.current?.(data)
        }
      } catch (err) {
        clearInterval(id)
        stop()
        onErrorRef.current?.(err)
      }
    }, intervalMs)

    return () => clearInterval(id)
  }, [enabled, fetcher, intervalMs, maxAttempts, stop])

  return { polling, stop }
}