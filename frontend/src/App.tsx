import { useState, useEffect, useRef, useCallback } from 'react'
import { marked } from 'marked'
import { fetchAgents, type Agent, streamMessage, API_BASE } from './api'
import { useChatStore, type ChatMessage } from './store'
import { Plus, Menu, Send, Bot, Shield, CreditCard, TrendingUp, Settings, Globe, FileCheck, AlertCircle, Zap, Sparkles, User, AlertTriangle } from 'lucide-react'
import LandingPage from './LandingPage'
import EnhancedAuth from './EnhancedAuth'
import './index.css'
import './App.css'
import './LandingPage.css'

// Configure marked for safe rendering
marked.setOptions({ breaks: true, gfm: true })

const AGENT_CONFIG: Record<string, { color: string; icon: any; short: string }> = {
  'Supervisor Router':      { color: '#6366f1', icon: Bot, short: 'Supervisor' },
  'Technical Specialist':   { color: '#06b6d4', icon: Settings, short: 'Technical' },
  'Account Security Agent': { color: '#f59e0b', icon: Shield, short: 'Security' },
  'Billing Finance Agent':  { color: '#22c55e', icon: CreditCard, short: 'Billing' },
  'Success Retention Agent':{ color: '#8b5cf6', icon: TrendingUp, short: 'Success' },
  'Operations Sync Agent':  { color: '#ec4899', icon: Settings, short: 'Ops' },
  'Linguistic Agent':       { color: '#0ea5e9', icon: Globe, short: 'Linguistic' },
  'Audit Agent':            { color: '#ef4444', icon: FileCheck, short: 'Audit' },
  'Guardrail':              { color: '#ef4444', icon: AlertCircle, short: 'Guardrail' },
  'System':                 { color: '#6b7280', icon: AlertCircle, short: 'System' },
}

function getAgentConfig(name: string) {
  return AGENT_CONFIG[name] || { color: '#6366f1', icon: Bot, short: name?.split(' ')[0] || 'AI' }
}

const QUICK_PROMPTS = [
  { text: 'Check invoice INV-2026-0301 for ahmed@techvista.pk' },
  { text: "My account is locked, email bilal@datapulse.pk" },
  { text: "Our API returns 502 errors on user-service, im sara@novabyte.io" },
  { text: "Show health score and feature adoption for sara@novabyte.io" },
]

function TypingDots({ agentName }: { agentName?: string }) {
  return (
    <div className="typing-indicator-container">
      {agentName && agentName !== 'System' && <div className="typing-agent-name">{agentName} is typing</div>}
      <div className="typing-dots">
        <span /><span /><span />
      </div>
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
        <div className="msg-avatar" style={{ background: `${cfg.color}18`, border: `1px solid ${cfg.color}30`, color: cfg.color }}>
          <cfg.icon size={16} />
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
          ) : msg.isStreaming && !msg.content ? (
            <TypingDots agentName={msg.agent_name} />
          ) : (
            <div className="md" dangerouslySetInnerHTML={{ __html: htmlContent || '' }} />
          )}
        </div>
        {msg.needs_approval && msg.approval_items && (
          <div className="approval-notice">
            <AlertTriangle size={14} />
            <span>Requires manager approval: <strong>{msg.approval_items.join(', ')}</strong></span>
          </div>
        )}
      </div>
      {isUser && (
        <div className="msg-avatar user-avatar">
          <User size={14} />
        </div>
      )}
    </div>
  )
}

export default function App() {
  const store = useChatStore()
  const user = store.user
  const [showLanding, setShowLanding] = useState(!user)

  useEffect(() => {
    setShowLanding(!user)
  }, [user])

  if (showLanding) {
    return <LandingPage onGetStarted={() => setShowLanding(false)} />
  }

  if (!user) {
    return <EnhancedAuth />
  }

  return <ChatApp />
}

function AuthOverlay() {
  const store = useChatStore()
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/signup'
      const body = isLogin ? { email, password } : { email, password, name }
      const res = await fetch(API_BASE + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Auth failed')
      store.setUser({ email: data.email, name: data.name, token: data.access_token })
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <div className="auth-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg-0)' }}>
      <form onSubmit={handleSubmit} style={{ background: 'var(--bg-1)', padding: '32px', borderRadius: '24px', border: '1px solid var(--border)', width: '360px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h2 style={{ textAlign: 'center' }}>Actuator AI</h2>
        <div style={{ display: 'flex', gap: '8px', background: 'var(--bg-2)', padding: '4px', borderRadius: '8px' }}>
          <button type="button" onClick={() => setIsLogin(true)} style={{ flex: 1, padding: '8px', border: 'none', background: isLogin ? 'var(--accent)' : 'transparent', color: '#fff', borderRadius: '4px', cursor: 'pointer' }}>Login</button>
          <button type="button" onClick={() => setIsLogin(false)} style={{ flex: 1, padding: '8px', border: 'none', background: !isLogin ? 'var(--accent)' : 'transparent', color: '#fff', borderRadius: '4px', cursor: 'pointer' }}>Sign Up</button>
        </div>
        {!isLogin && <input type="text" placeholder="Name" value={name} onChange={e => setName(e.target.value)} required className="email-input" style={{ width: '100%', border: '1px solid var(--border)', padding: '10px 14px', borderRadius: '8px' }} />}
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required className="email-input" style={{ width: '100%', border: '1px solid var(--border)', padding: '10px 14px', borderRadius: '8px' }} />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required className="email-input" style={{ width: '100%', border: '1px solid var(--border)', padding: '10px 14px', borderRadius: '8px' }} />
        {error && <div style={{ color: 'var(--red)', fontSize: '12px', textAlign: 'center' }}>{error}</div>}
        <button type="submit" style={{ padding: '12px', background: 'var(--accent)', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}>{isLogin ? 'Log In' : 'Sign Up'}</button>
      </form>
    </div>
  )
}

function ChatApp() {
  const store = useChatStore()
  const messages = store.messages
  const conversationId = store.conversationId
  const loading = store.loading
  const activeAgent = store.activeAgent

  const [input, setInput] = useState('')
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

  const handleSend = useCallback((overrideText?: string) => {
    const text = (overrideText ?? input).trim()
    if (!text || loading) return

    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    streamMessage(text, store.user?.email || 'guest@example.com', conversationId)
  }, [input, conversationId, loading, store.user])

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
    store.clear()
  }

  const isEmpty = messages.length === 0

  return (
    <div className="app">
      {/* SIDEBAR */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-top">
          <div className="logo">
            <div className="logo-icon">
              <Zap size={18} />
            </div>
            {sidebarOpen && (
              <div className="logo-text">
                <div className="logo-name">Actuator AI</div>
                <div className="logo-sub">Multi-Agent Platform</div>
              </div>
            )}
          </div>
          <button className="new-chat-btn" onClick={newConversation} title="New conversation">
            {sidebarOpen ? (
              <><Plus size={14} /> New Chat</>
            ) : (
              <Plus size={14} />
            )}
          </button>
        </div>

        {sidebarOpen && (
          <>
            <div className="sidebar-section-label">Active Agents</div>
            <div className="agent-list">
              {(agents.length > 0 ? agents : Object.entries(AGENT_CONFIG).slice(0, 8).map(([, _v], i) => ({
                key: String(i), name: Object.keys(AGENT_CONFIG)[i], description: '', tool_count: 0
              }))).map((a) => {
                const cfg = getAgentConfig(a.name)
                return (
                  <div className="agent-item" key={a.key}>
                    <div className="agent-dot" style={{ background: cfg.color }} />
                    <span className="agent-item-name">{a.name}</span>
                  </div>
                )
              })}
            </div>

            <div className="sidebar-footer">
              <div className="status-pill" style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                <span>{store.user?.name || 'Guest'}</span>
                <span style={{ cursor: 'pointer', color: 'var(--accent)' }} onClick={() => store.logout()}>Logout</span>
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
            <button className="toggle-btn" onClick={() => setSidebarOpen(prev => !prev)} title="Toggle sidebar">
              <Menu size={16} />
            </button>
            <div className="conv-info">
              <span className="conv-title">{conversationId ? 'Active Conversation' : 'New Chat'}</span>
              {conversationId && <span className="conv-id">{conversationId.slice(0, 8)}…</span>}
            </div>
          </div>
          <div className="email-field">
            <span style={{ fontSize: '13px', fontWeight: 500 }}>{store.user?.email}</span>
          </div>
        </div>

        {/* Chat area */}
        <div className="chat-area">
          {isEmpty ? (
            <div className="welcome">
              <div className="welcome-orb" />
              <div className="welcome-icon">
                <Sparkles size={28} />
              </div>
              <h1 className="welcome-title">How can I help?</h1>
              <p className="welcome-sub">Route your request to one of 8 specialist agents — billing, technical, security, success, operations, linguistic, or audit.</p>
              <div className="quick-prompts">
                {QUICK_PROMPTS.map((q, i) => (
                  <button key={i} className="quick-prompt" onClick={() => handleSend(q.text)}>
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
              {loading && activeAgent !== 'System' && messages[messages.length-1]?.role !== 'assistant' && (
                <div className="msg-row ai">
                  <div className="msg-content">
                     <div className="ai-bubble msg-bubble"><TypingDots agentName={activeAgent} /></div>
                  </div>
                </div>
              )}
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
                <Send size={16} />
              )}
            </button>
          </div>
          <div className="input-hint">Enter to send · Shift+Enter for new line</div>
        </div>
      </main>
    </div>
  )
}
