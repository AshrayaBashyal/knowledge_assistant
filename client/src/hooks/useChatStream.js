import { useCallback, useRef, useState } from 'react'
import { readSSEStream } from '../lib/sse'
import { streamChat } from '../services/chatService'
import { getErrorMessage } from '../lib/errors'

// All the state a streaming chat turn needs:
// - streaming: true while tokens are arriving
// - streamingText: the accumulated partial response
// - toolCalls: tool_call events seen so far this turn
// - sources: sources event payload if search_my_knowledge ran
// - error: stream-level error (note: HTTP status is always 200, error is in the stream body)
export function useChatStream({ onMetaReceived, onDone }) {
  const [streaming, setStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  const [toolCalls, setToolCalls] = useState([])
  const [sources, setSources] = useState(null)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const send = useCallback(async ({ message, conversationId }) => {
    // Cancel any in-flight stream before starting a new one.
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setStreaming(true)
    setStreamingText('')
    setToolCalls([])
    setSources(null)
    setError(null)

    try {
      const response = await streamChat({ message, conversationId })

      if (!response.ok) {
        throw new Error(`Stream request failed (${response.status})`)
      }

      let resolvedConversationId = conversationId
      let fullText = ''
      let resolvedSources = null  // track locally so the done handler isn't reading stale closure state

      for await (const frame of readSSEStream(response)) {
        if (controller.signal.aborted) break

        switch (frame.event) {
          case 'meta':
            // The backend assigns a conversation ID if we didn't send one.
            resolvedConversationId = frame.data.conversation_id
            onMetaReceived?.(frame.data.conversation_id)
            break

          case 'tool_call':
            setToolCalls((prev) => [...prev, frame.data.tool])
            break

          case 'sources':
            resolvedSources = frame.data.sources
            setSources(resolvedSources)  // also update state so ToolCallIndicator can show them mid-stream
            break

          case 'token':
            fullText += frame.data.content
            setStreamingText(fullText)
            break

          case 'done':
            setStreaming(false)
            onDone?.({ text: fullText, conversationId: resolvedConversationId, sources: resolvedSources })
            break

          case 'error':
            // Backend sends HTTP 200 even for stream errors - the error
            // only appears as an event in the body.
            throw new Error(frame.data.detail ?? 'Stream error')
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(getErrorMessage(err))
        setStreaming(false)
      }
    }
  }, [onMetaReceived, onDone])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setStreaming(false)
  }, [])

  return { send, cancel, streaming, streamingText, toolCalls, sources, error }
}