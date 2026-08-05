import { useCallback, useEffect, useState } from 'react'

// Most list pages do the same thing: fetch on mount, track loading/error,
// expose a way to re-fetch after a mutation. This hook captures that pattern
// once so each page doesn't wire up the same three useState calls itself.
export function useResourceList(fetcher) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetcher()
      setItems(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }, [fetcher])

  useEffect(() => {
    load()
  }, [load])

  return { items, setItems, loading, error, reload: load }
}