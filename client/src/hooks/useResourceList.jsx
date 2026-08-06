import { useCallback, useEffect, useRef, useState } from 'react'

// Most list pages do the same thing: fetch on mount, track loading/error,
// expose a way to re-fetch after a mutation. This hook captures that pattern
// once so each page doesn't wire up the same three useState calls itself.
//
// The fetcher is stored in a ref so that an unstable reference (e.g. an
// inline arrow function passed from a parent) doesn't trigger a re-fetch
// on every render. Only the initial mount ever fires the fetch automatically;
// call reload() explicitly to re-fetch after a mutation.
export function useResourceList(fetcher) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const fetcherRef = useRef(fetcher)

  // Keep the ref current without making it a useCallback dependency.
  useEffect(() => { fetcherRef.current = fetcher })

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetcherRef.current()
      setItems(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }, []) // stable - never recreated

  useEffect(() => {
    load()
  }, [load]) // fires once on mount

  return { items, setItems, loading, error, reload: load }
}