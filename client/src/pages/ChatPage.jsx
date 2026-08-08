import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PaperPlaneTilt, Stop, Trash } from '@phosphor-icons/react'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import Alert from '../components/ui/Alert'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import ChatMessage from '../components/chat/ChatMessage'
import ToolCallIndicator from '../components/chat/ToolCallIndicator'
import { useChatStream } from '../hooks/useChatStream'
import { useConversations } from '../lib/ConversationsContext'
import { fetchConversation } from '../services/chatService'
import { getErrorMessage } from '../lib/errors'

export default function ChatPage() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const { addConversation, updateConversation, removeConversation } = useConversations()

  const [messages, setMessages] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [input, setInput] = useState('')
  const [toDelete, setToDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // When a new conversation_id arrives from the meta event, navigate to
  // its URL so the sidebar can highlight the right entry and the URL is
  // shareable / bookmarkable.
  const handleMeta = useCallback((id) => {
    if (!conversationId) {
      navigate(`/chat/${id}`, { replace: true })
    }
  }, [conversationId, navigate])

  const handleStreamDone = useCallback(({ text, conversationId: id, sources }) => {
    const assistantMessage = {
      id: Date.now(),
      role: 'assistant',
      content: text,
      created_at: new Date().toISOString(),
      sources: sources ?? null,
    }
    setMessages((prev) => [...prev, assistantMessage])
    // Update the conversation's updated_at in the sidebar list.
    if (id) updateConversation(id, { updated_at: new Date().toISOString() })
  }, [updateConversation])

  const { send, cancel, streaming, streamingText, toolCalls, sources, error: streamError } = useChatStream({
    onMetaReceived: handleMeta,
    onDone: handleStreamDone,
  })

  // Load history when switching to an existing conversation.
  useEffect(() => {
    if (!conversationId) {
      setMessages([])
      return
    }
    let cancelled = false
    async function load() {
      setLoadingHistory(true)
      try {
        const data = await fetchConversation(conversationId)
        if (!cancelled) setMessages(data.messages ?? [])
      } catch {
        // If the conversation doesn't exist, go back to /chat.
        if (!cancelled) navigate('/chat', { replace: true })
      } finally {
        if (!cancelled) setLoadingHistory(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [conversationId, navigate])

  // Auto-scroll to the bottom whenever messages or streaming text changes.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  // Re-focus the input after streaming finishes so the user can type immediately.
  useEffect(() => {
    if (!streaming) inputRef.current?.focus()
  }, [streaming])

  // Focus input after history loads too.
  useEffect(() => {
    if (!loadingHistory) inputRef.current?.focus()
  }, [loadingHistory])

  async function handleSend() {
    const text = input.trim()
    if (!text || streaming) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    // Reset the auto-grown textarea back to one row.
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
    }

    const isNew = !conversationId
    await send({ message: text, conversationId: conversationId ? Number(conversationId) : undefined })

    // If this was a brand new conversation, add it to the sidebar list.
    // The actual ID comes via handleMeta and the navigate() call there,
    // but we add a provisional entry now so the sidebar isn't empty.
    if (isNew) {
      addConversation({
        id: null, // will be corrected when the page navigates to /chat/:id
        title: text.slice(0, 60),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  async function handleDeleteConversation() {
    if (!conversationId) return
    setDeleting(true)
    try {
      await removeConversation(Number(conversationId))
      navigate('/chat', { replace: true })
    } catch (err) {
      // removeConversation throws if the DELETE fails
    } finally {
      setDeleting(false)
      setToDelete(false)
    }
  }

  const showStreamingBubble = streaming && streamingText

  return (
    <div className="flex h-full flex-col rounded-card border border-mist bg-paper">
      {/* Conversation toolbar */}
      {conversationId && (
        <div className="flex items-center justify-end border-b border-mist px-4 py-2">
          <button
            onClick={() => setToDelete(true)}
            className="flex items-center gap-1.5 rounded-tab px-2 py-1.5 text-xs text-ink-soft hover:text-crimson"
            title="Delete conversation"
          >
            <Trash size={14} /> Delete
          </button>
        </div>
      )}

      {/* Message thread */}
      <div
        className="flex-1 space-y-5 overflow-y-auto px-6 py-6"
        aria-label="Conversation"
        aria-live="polite"
        aria-atomic="false"
      >
        {loadingHistory && (
          <div className="flex justify-center py-8">
            <Spinner size={24} className="text-ink-soft" />
          </div>
        )}

        {!loadingHistory && messages.length === 0 && !streaming && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
            <p className="font-display italic text-2xl text-ink">Start a conversation</p>
            <p className="max-w-sm text-sm text-ink-soft">
              Ask about your documents, notes, or anything else. The assistant can search
              your knowledge base and remember facts for you.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {/* Live streaming bubble */}
        {showStreamingBubble && (
          <ChatMessage
            message={{ role: 'assistant', content: streamingText }}
            isStreaming
          />
        )}

        {/* Tool call indicator shown while tools run, before tokens start */}
        {streaming && !streamingText && (
          <div className="flex justify-start">
            <div className="max-w-[75%] rounded-card border border-mist bg-paper-dim px-4 py-3">
              <ToolCallIndicator tools={toolCalls} sources={sources} />
              {!toolCalls.length && (
                <div className="flex items-center gap-2 text-xs text-ink-soft">
                  <Spinner size={13} />
                  <span className="font-mono">Thinking…</span>
                </div>
              )}
            </div>
          </div>
        )}

        {streamError && (
          <Alert variant="error" className="mx-auto max-w-md">{streamError}</Alert>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="flex items-end gap-3 border-t border-mist p-4">
        <textarea
          ref={inputRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message the assistant… (Shift+Enter for new line)"
          disabled={streaming}
          className="flex-1 resize-none rounded-tab border border-mist bg-paper px-3 py-2 text-sm text-ink placeholder:text-ink-soft focus:outline-none focus:ring-1 focus:ring-ledger disabled:opacity-50"
          style={{ maxHeight: '160px', overflowY: 'auto' }}
          onInput={(e) => {
            // Auto-grow the textarea as the user types.
            e.target.style.height = 'auto'
            e.target.style.height = `${e.target.scrollHeight}px`
          }}
        />
        {streaming ? (
          <Button variant="ghost" onClick={cancel} title="Stop generating">
            <Stop size={16} weight="fill" /> Stop
          </Button>
        ) : (
          <Button onClick={handleSend} disabled={!input.trim()}>
            <PaperPlaneTilt size={16} />
            Send
          </Button>
        )}
      </div>

      {toDelete && (
        <ConfirmDialog
          title="Delete conversation"
          message="This conversation and all its messages will be permanently deleted."
          onConfirm={handleDeleteConversation}
          onCancel={() => setToDelete(false)}
          busy={deleting}
        />
      )}
    </div>
  )
}