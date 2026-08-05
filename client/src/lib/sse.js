// The chat endpoint streams Server-Sent Events over a POST response, which
// rules out the built-in EventSource (GET-only). This is a generic reader
// for that shape - it knows nothing about chat specifically, just how to
// turn a streaming Response body into {event, data} frames as they arrive.
//
// Usage:
//   for await (const frame of readSSEStream(response)) {
//     // frame.event is the event name ("meta", "token", "done", ...)
//     // frame.data is the already-JSON.parsed payload
//   }
export async function* readSSEStream(response) {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // SSE frames are separated by a blank line
      let boundary
      while ((boundary = buffer.indexOf('\n\n')) !== -1) {
        const rawFrame = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        const frame = parseFrame(rawFrame)
        if (frame) yield frame
      }
    }
  } finally {
    reader.releaseLock()
  }
}

function parseFrame(rawFrame) {
  let event = 'message'
  let dataLines = []

  for (const line of rawFrame.split('\n')) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim())
    }
  }

  if (dataLines.length === 0) return null

  const rawData = dataLines.join('\n')
  try {
    return { event, data: JSON.parse(rawData) }
  } catch {
    return { event, data: rawData }
  }
}