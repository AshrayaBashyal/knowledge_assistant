import { useEffect, useState } from 'react'

// Waits until the user pauses typing before updating the returned value.
// Keeps search from firing a request on every single keystroke.
export function useDebounce(value, delayMs = 350) {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(id)
  }, [value, delayMs])

  return debounced
}