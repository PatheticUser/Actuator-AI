import { useState, useEffect, useRef, useCallback } from 'react'
import { marked } from 'marked'
import { sendMessage, fetchAgents, type Agent, type Message, type ChatResponse } from './api'
import './index.css'
import './App.css'

// Configure marked for safe rendering
marked.setOptions({ breaks: true, gfm: true })

const AGENT_CONFIG: Record<string, { color: string; emoji: string; short: string }> = {
  'Supervisor Router':      { color: '#6366f1', emoji: '🎯', short: 'Supervisor' },
  'Technical Specialist':   { color: '#06b6d4', emoji: '🔧', short: 'Technical' },
  'Account Security Agent': { color: '#f59e0b', emoji: '🔒', short: 'Security' },
  'Billing Finance Agent':  { color: '#22c55e', emoji: '💳', short: 'Billing' },
  'Success Retention Agent':{ color: '#8b5cf6', emoji: '📈', short: 'Success' },
  'Operations Sync Agent':  { color: '#ec4899', emoji: '⚙️', short: 'Ops' },
  'Linguistic Agent':       { color: '#0ea5e9', emoji: '🌐', short: 'Linguistic' },
  'Audit Agent':            { color: '#ef4444', emoji: '🔍', short: 'Audit' },
  'Guardrail':              { color: '#ef4444', emoji: '🛡️', short: 'Guardrail' },
  'System':                 { color: '#6b7280', emoji: '⚡', short: 'System' },
}

function getAgentConfig(name: string) {
  return AGENT_CONFIG[name] || { color: '#6366f1', emoji: '⚡', short: name?.split(' ')[0] || 'AI' }
}

interface ChatMessage extends Message {
  needs_approval?: boolean
  approval_items?: string[]
  isStreaming?: boolean
}

const QUICK_PROMPTS = [
  { icon: '📄', text: 'Check invoice INV-2026-0301 for ahmed@techvista.pk' },
  { icon: '🔒', text: "My account is locked, email bilal@datapulse.pk" },
  { icon: '🔧', text: "Our API returns 502 errors on user-service, im sara@novabyte.io" },
  { icon: '📊', text: "Show health score and feature adoption for sara@novabyte.io" },
]

function TypingDots() {
  return (
    <div className="typing-dots">
      <span /><span /><span />
    </div>
  )
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user'
  const cfg = getAgentConfig(msg.agent_name || 'System')
  const htmlContent = !isUser
    ? (marked.parse(msg.content) as string)
    : null

  return (
    <div className={`msg-row ${isUser ? 'user' : 'ai'}`}>
      {!isUser && (
        <div className="msg-avatar" style={{ background: `${cfg.color}18`, border: `1px solid ${cfg.color}30` }}>
          <span className="avatar-emoji">{cfg.emoji}</span>
        </div>
      )}
      <div className="msg-content">
        {!isUser && (
          <div className="msg-meta">
            <span className="agent-badge" style={{ background: `${cfg.color}15`, color: cfg.color, border: `1px solid ${cfg.color}30` }}>
              {cfg.short}
            </span>
          </div>
        )}
        <div className={`msg-bubble ${isUser ? 'user-bubble' : 'ai-bubble'}`}>
          {isUser ? (
            <span>{msg.content}</span>
          ) : msg.isStreaming ? (
            <TypingDots />
          ) : (
            <div className="md" dangerouslySetInnerHTML={{ __html: htmlContent || '' }} />
          )}
        </div>
        {msg.needs_approval && msg.approval_items && (
          <div className="approval-notice">
            <span className="approval-icon">⚠️</span>
            <span>Requires manager approval: <strong>{msg.approval_items.join(', ')}</strong></span>
          </div>
        )}
      </div>
      {isUser && (
        <div className="msg-avatar user-avatar">
          <span className="avatar-emoji">👤</span>
        </div>
      )}
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [email, setEmail] = useState('ahmed@techvista.pk')
  const [conversationId, setConversationId] = useState<string | undefined>()
  const [loading, setLoading] = useState(false)
  const [agents, setAgents] = useState<Agent[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    fetchAgents().then(setAgents).catch(() => {})
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(async (overrideText?: string) => {
    const text = (overrideText ?? input).trim()
    if (!text || loading) return

    const userMsg: ChatMessage = { role: 'user', content: text }
    const streamingMsg: ChatMessage = { role: 'assistant', content: '', agent_name: 'System', isStreaming: true }

    setMessages(prev => [...prev, userMsg, streamingMsg])
    setInput('')
    setLoading(true)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    try {
      const data: ChatResponse = await sendMessage(text, email, conversationId)
      if (data.conversation_id) setConversationId(data.conversation_id)

      setMessages(prev => {
        const next = [...prev]
        next[next.length - 1] = {
          role: 'assistant',
          content: data.response,
          agent_name: data.agent_name,
          needs_approval: data.needs_approval,
          approval_items: data.approval_items,
          isStreaming: false,
        }
        return next
      })
    } catch {
      setMessages(prev => {
        const next = [...prev]
        next[next.length - 1] = {
          role: 'assistant',
          content: '**Connection error.** Is the FastAPI server running on port 8000?',
          agent_name: 'System',
          isStreaming: false,
        }
        return next
      })
    } finally {
      setLoading(false)
    }
  }, [input, email, conversationId, loading])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
  }

  const newConversation = () => {
    setMessages([])
    setConversationId(undefined)
  }

  const isEmpty = messages.length === 0

  return (
    <div className="app">
      {/* SIDEBAR */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-top">
          <div className="logo">
            <div className="logo-icon">⚡</div>
            {sidebarOpen && (
              <div className="logo-text">
                <div className="logo-name">Actuator AI</div>
                <div className="logo-sub">Multi-Agent Platform</div>
              </div>
            )}
          </div>
          <button className="new-chat-btn" onClick={newConversation} title="New conversation">
            {sidebarOpen ? (
              <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> New Chat</>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            )}
          </button>
        </div>

        {sidebarOpen && (
          <>
            <div className="sidebar-section-label">Active Agents</div>
            <div className="agent-list">
              {(agents.length > 0 ? agents : Object.entries(AGENT_CONFIG).slice(0, 8).map(([, v], i) => ({
                key: String(i), name: Object.keys(AGENT_CONFIG)[i], description: '', tool_count: 0
              }))).map((a) => {
                const cfg = getAgentConfig(a.name)
                return (
                  <div className="agent-item" key={a.key}>
                    <div className="agent-dot" style={{ background: cfg.color }} />
                    <span className="agent-item-name">{a.name}</span>
                    {a.tool_count > 0 && <span className="agent-tools-badge">{a.tool_count}t</span>}
                  </div>
                )
              })}
            </div>

            <div className="sidebar-footer">
              <div className="status-pill">
                <div className="status-dot" />
                <span>8 agents · MCP live</span>
              </div>
            </div>
          </>
        )}
      </aside>

      {/* MAIN */}
      <main className="main">
        {/* Topbar */}
        <div className="topbar">
          <div className="topbar-left">
            <button className="toggle-btn" onClick={() => setSidebarOpen(v => !v)} title="Toggle sidebar">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
              </svg>
            </button>
            <div className="conv-info">
              <span className="conv-title">{conversationId ? 'Active Conversation' : 'New Chat'}</span>
              {conversationId && <span className="conv-id">{conversationId.slice(0, 8)}…</span>}
            </div>
          </div>
          <div className="email-field">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
            <input
              type="text"
              className="email-input"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="customer@company.com"
            />
          </div>
        </div>

        {/* Chat area */}
        <div className="chat-area">
          {isEmpty ? (
            <div className="welcome">
              <div className="welcome-orb" />
              <div className="welcome-icon">⚡</div>
              <h1 className="welcome-title">How can I help?</h1>
              <p className="welcome-sub">Route your request to one of 8 specialist agents — billing, technical, security, success, operations, linguistic, or audit.</p>
              <div className="quick-prompts">
                {QUICK_PROMPTS.map((q, i) => (
                  <button key={i} className="quick-prompt" onClick={() => handleSend(q.text)}>
                    <span className="qp-icon">{q.icon}</span>
                    <span>{q.text}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((msg, i) => (
                <MessageBubble key={i} msg={msg} />
              ))}
              <div ref={chatEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="input-area">
          <div className={`input-box ${loading ? 'loading' : ''}`}>
            <textarea
              ref={textareaRef}
              className="input-textarea"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Describe your issue or request…"
              rows={1}
              disabled={loading}
            />
            <button
              className={`send-btn ${(!input.trim() || loading) ? 'disabled' : ''}`}
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
            >
              {loading ? (
                <div className="send-spinner" />
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              )}
            </button>
          </div>
          <div className="input-hint">Enter to send · Shift+Enter for new line</div>
        </div>
      </main>
    </div>
  )
}
