import { create } from 'zustand'
import type { Message } from './api'

export interface ChatMessage extends Message {
  needs_approval?: boolean
  approval_items?: string[]
  isStreaming?: boolean
}

interface ChatStore {
  messages: ChatMessage[]
  conversationId?: string
  loading: boolean
  activeAgent: string
  setMessages: (messages: ChatMessage[]) => void
  addMessage: (message: ChatMessage) => void
  updateLastMessage: (updater: (msg: ChatMessage) => ChatMessage) => void
  setConversationId: (id: string | undefined) => void
  setLoading: (loading: boolean) => void
  setActiveAgent: (agent: string) => void
  clear: () => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  conversationId: undefined,
  loading: false,
  activeAgent: 'System',
  
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
  setLoading: (loading) => set({ loading }),
  setActiveAgent: (activeAgent) => set({ activeAgent }),
  clear: () => set({ messages: [], conversationId: undefined, loading: false, activeAgent: 'System' })
}))
