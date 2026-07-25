import { create } from 'zustand'
import type { Message } from './api'

export interface ChatMessage extends Message {
  needs_approval?: boolean
  approval_items?: string[]
  isStreaming?: boolean
  images?: string[]
}

export interface ConversationItem {
  id: string
  summary?: string
  customer_email?: string
  started_at: string
  status?: string
}

interface ChatStore {
  user: { email: string; name: string; token: string } | null
  messages: ChatMessage[]
  conversationId?: string
  conversationsHistory: ConversationItem[]
  loading: boolean
  activeAgent: string
  setUser: (user: { email: string; name: string; token: string } | null) => void
  logout: () => void
  setMessages: (messages: ChatMessage[]) => void
  addMessage: (message: ChatMessage) => void
  updateLastMessage: (updater: (msg: ChatMessage) => ChatMessage) => void
  setConversationId: (id: string | undefined) => void
  setConversationsHistory: (list: ConversationItem[]) => void
  removeConversationFromHistory: (id: string) => void
  setLoading: (loading: boolean) => void
  setActiveAgent: (agent: string) => void
  clear: () => void
}

export const useChatStore = create<ChatStore>((set) => ({
  user: null,
  messages: [],
  conversationId: undefined,
  conversationsHistory: [],
  loading: false,
  activeAgent: 'System',
  
  setUser: (user) => set({ user }),
  logout: () => set({ user: null, messages: [], conversationId: undefined, conversationsHistory: [], activeAgent: 'System' }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  updateLastMessage: (updater) => set((state) => {
    if (state.messages.length === 0) return state
    const newMessages = [...state.messages]
    const lastIdx = newMessages.length - 1
    newMessages[lastIdx] = updater(newMessages[lastIdx])
    return { messages: newMessages }
  }),
  setConversationId: (id) => set({ conversationId: id }),
  setConversationsHistory: (conversationsHistory) => set({ conversationsHistory }),
  removeConversationFromHistory: (id) => set((state) => ({
    conversationsHistory: state.conversationsHistory.filter(c => c.id !== id),
    conversationId: state.conversationId === id ? undefined : state.conversationId,
    messages: state.conversationId === id ? [] : state.messages
  })),
  setLoading: (loading) => set({ loading }),
  setActiveAgent: (activeAgent) => set({ activeAgent }),
  clear: () => set({ messages: [], conversationId: undefined, loading: false, activeAgent: 'System' })
}))
