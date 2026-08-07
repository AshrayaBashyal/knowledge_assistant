import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { fetchConversations, deleteConversation, renameConversation } from '../services/chatService'

const ConversationsContext = createContext(null)

export function ConversationsProvider({ children }) {
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchConversations()
      setConversations(data)
    } catch {
      // Sidebar failing to load conversations shouldn't break the whole app.
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { reload() }, [reload])

  const addConversation = useCallback((convo) => {
    setConversations((prev) => [convo, ...prev])
  }, [])

  const updateConversation = useCallback((id, changes) => {
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...changes } : c))
    )
  }, [])

  const removeConversation = useCallback(async (id) => {
    await deleteConversation(id)
    setConversations((prev) => prev.filter((c) => c.id !== id))
  }, [])

  const rename = useCallback(async (id, title) => {
    const updated = await renameConversation(id, title)
    updateConversation(id, { title: updated.title })
  }, [updateConversation])

  return (
    <ConversationsContext.Provider value={{
      conversations, loading, reload,
      addConversation, updateConversation, removeConversation, rename,
    }}>
      {children}
    </ConversationsContext.Provider>
  )
}

export function useConversations() {
  const ctx = useContext(ConversationsContext)
  if (!ctx) throw new Error('useConversations must be used within a ConversationsProvider')
  return ctx
}