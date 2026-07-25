import { useState, useEffect, useRef, useCallback } from 'react'
import { marked } from 'marked'
import { fetchAgents, type Agent, streamMessage, fetchUserConversations, fetchMessages, deleteConversationApi } from './api'
import { useChatStore, type ChatMessage } from './store'
import { Plus, Menu, Send, Bot, Shield, CreditCard, TrendingUp, Settings, Globe, FileCheck, AlertCircle, Zap, Sparkles, User, AlertTriangle, Paperclip, FileText, X, MessageSquare, Trash2, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import LandingPage from './LandingPage'
import EnhancedAuth from './EnhancedAuth'
import Docs from './Docs'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
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
  { text: 'How do I upgrade to the Enterprise plan?' },
  { text: 'Translate customer issue to Spanish & check sentiment' },
  { text: 'Generate audit compliance report for last 10 requests' }
]

function TypingDots({ agentName }: { agentName?: string }) {
  const cfg = getAgentConfig(agentName || 'Supervisor Router')
  const Icon = cfg.icon
  return (
    <div className="typing-indicator">
      <div className="agent-badge" style={{ background: `${cfg.color}15`, color: cfg.color, borderColor: `${cfg.color}30` }}>
        <Icon size={12} />
        <span>{agentName || 'Thinking...'}</span>
      </div>
      <div className="dots">
        <span />
        <span />
        <span />
      </div>
    </div>
  )
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user'
  const cfg = getAgentConfig(msg.agent_name || 'Supervisor Router')
  const AgentIcon = cfg.icon

  const htmlContent = isUser ? null : marked.parse(msg.content)

  return (
    <div className={`message-row ${isUser ? 'user-row' : 'assistant-row'}`}>
      {!isUser && (
        <div className="msg-avatar" style={{ background: `${cfg.color}20`, color: cfg.color, borderColor: `${cfg.color}40` }}>
          <AgentIcon size={14} />
        </div>
      )}
      <div className="message-content">
        {!isUser && msg.agent_name && (
          <div className="agent-tag" style={{ color: cfg.color }}>
            {msg.agent_name.toUpperCase()}
          </div>
        )}
        <div className={`bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
          {isUser ? (
            <div>
              {msg.images && msg.images.length > 0 && (
                <div className="msg-images-preview">
                  {msg.images.map((img, idx) => (
                    <img key={idx} src={img} alt="attachment" className="msg-attached-img" />
                  ))}
                </div>
              )}
              <span>{msg.content}</span>
            </div>
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
  const navigate = useNavigate()

  return (
    <Routes>
      <Route path="/" element={user ? <ChatApp /> : <LandingPage onGetStarted={() => navigate('/login')} />} />
      <Route path="/login" element={user ? <Navigate to="/" /> : <EnhancedAuth />} />
      <Route path="/docs" element={<Docs />} />
    </Routes>
  )
}

interface AttachedFile {
  name: string
  type: 'image' | 'file'
  dataUrl?: string
  textContent?: string
}

function ChatApp() {
  const store = useChatStore()
  const messages = store.messages
  const conversationId = store.conversationId
  const conversationsHistory = store.conversationsHistory
  const loading = store.loading
  const activeAgent = store.activeAgent

  const [input, setInput] = useState('')
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchAgents().then(setAgents).catch(() => {})
  }, [])

  // Load conversations list for logged-in user
  useEffect(() => {
    if (store.user?.email) {
      fetchUserConversations(store.user.email)
        .then(list => store.setConversationsHistory(list))
        .catch(() => {})
    }
  }, [store.user?.email])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return
    Array.from(files).forEach(file => {
      const isImg = file.type.startsWith('image/')
      const reader = new FileReader()
      if (isImg) {
        reader.onload = (evt) => {
          if (evt.target?.result) {
            setAttachedFiles(prev => [...prev, { name: file.name, type: 'image', dataUrl: evt.target!.result as string }])
          }
        }
        reader.readAsDataURL(file)
      } else {
        reader.onload = (evt) => {
          if (evt.target?.result) {
            setAttachedFiles(prev => [...prev, { name: file.name, type: 'file', textContent: evt.target!.result as string }])
          }
        }
        reader.readAsText(file)
      }
    })
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleSend = useCallback((overrideText?: string) => {
    let text = (overrideText ?? input).trim()
    if ((!text && attachedFiles.length === 0) || loading) return

    const imgsToSend: string[] = []
    attachedFiles.forEach(f => {
      if (f.type === 'image' && f.dataUrl) {
        imgsToSend.push(f.dataUrl)
      } else if (f.type === 'file' && f.textContent) {
        text += `\n\n--- Attached File: ${f.name} ---\n${f.textContent.slice(0, 4000)}`
      }
    })

    setInput('')
    setAttachedFiles([])
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    streamMessage(text || 'Analyze attached file(s)', store.user?.email || 'guest@example.com', conversationId, imgsToSend)
  }, [input, attachedFiles, conversationId, loading, store.user])

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

  const handleLoadConv = async (id: string) => {
    store.setLoading(true)
    try {
      const msgs = await fetchMessages(id)
      store.setConversationId(id)
      store.setMessages(msgs.map(m => ({ ...m, role: m.role as 'user' | 'assistant' })))
    } catch (err) {
      console.error("Failed to load conversation", err)
    } finally {
      store.setLoading(false)
    }
  }

  const handleDeleteConv = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    try {
      await deleteConversationApi(id)
      store.removeConversationFromHistory(id)
    } catch (err) {
      console.error("Failed to delete conversation", err)
    }
  }

  const newConversation = () => {
    store.clear()
    setAttachedFiles([])
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
          <div className="sidebar-top-actions">
            <button className="new-chat-btn" onClick={newConversation} title="New conversation">
              {sidebarOpen ? (
                <><Plus size={14} /> New Chat</>
              ) : (
                <Plus size={14} />
              )}
            </button>
            <button className="toggle-sidebar-btn" onClick={() => setSidebarOpen(prev => !prev)} title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}>
              {sidebarOpen ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />}
            </button>
          </div>
        </div>

        {sidebarOpen && (
          <div className="sidebar-scroll-area">
            {/* CONVERSATION HISTORY (Claude / ChatGPT style) */}
            <div className="sidebar-section-label">Conversations</div>
            <div className="conversations-history-list">
              {conversationsHistory.length === 0 ? (
                <div className="empty-history-text">No past chats yet</div>
              ) : (
                conversationsHistory.map((c) => (
                  <div
                    key={c.id}
                    className={`conv-history-item ${conversationId === c.id ? 'active' : ''}`}
                    onClick={() => handleLoadConv(c.id)}
                    title={c.summary || c.id}
                  >
                    <MessageSquare size={14} className="conv-item-icon" />
                    <span className="conv-item-title">{c.summary || `Chat ${c.id.slice(0, 8)}`}</span>
                    <button
                      className="delete-conv-btn"
                      onClick={(e) => handleDeleteConv(e, c.id)}
                      title="Delete chat"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="sidebar-section-label" style={{ marginTop: '16px' }}>Active Agents</div>
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
          </div>
        )}

        {sidebarOpen && (
          <div className="sidebar-footer">
            <div className="status-pill" style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
              <span className="user-email-truncate">{store.user?.email || 'Guest'}</span>
              <span style={{ cursor: 'pointer', color: 'var(--accent)', fontWeight: 600 }} onClick={() => store.logout()}>Logout</span>
            </div>
          </div>
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
              {messages.filter(msg => (msg.content && msg.content.trim() !== '') || msg.isStreaming || (msg.images && msg.images.length > 0)).map((msg, i) => (
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
          {attachedFiles.length > 0 && (
            <div className="image-previews-container">
              {attachedFiles.map((file, idx) => (
                <div key={idx} className={`image-preview-item ${file.type === 'file' ? 'doc-item' : ''}`}>
                  {file.type === 'image' && file.dataUrl ? (
                    <img src={file.dataUrl} alt="preview" />
                  ) : (
                    <div className="doc-preview-badge">
                      <FileText size={16} />
                      <span className="doc-preview-name">{file.name}</span>
                    </div>
                  )}
                  <button className="remove-img-btn" onClick={() => removeFile(idx)}>
                    <X size={12} />
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className={`input-box ${loading ? 'loading' : ''}`}>
            <input
              type="file"
              ref={fileInputRef}
              accept="*/*"
              multiple
              style={{ display: 'none' }}
              onChange={handleFileSelect}
            />
            <button
              className="attach-btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
              title="Attach any file (documents, code, logs, images)"
            >
              <Paperclip size={18} />
            </button>
            <textarea
              ref={textareaRef}
              className="input-textarea"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Describe your issue or request (or attach files)…"
              rows={1}
              disabled={loading}
            />
            <button
              className={`send-btn ${((!input.trim() && attachedFiles.length === 0) || loading) ? 'disabled' : ''}`}
              onClick={() => handleSend()}
              disabled={(!input.trim() && attachedFiles.length === 0) || loading}
            >
              {loading ? (
                <div className="send-spinner" />
              ) : (
                <Send size={16} />
              )}
            </button>
          </div>
          <div className="input-hint">Enter to send · Shift+Enter for new line · Click paperclip to attach files</div>
        </div>
      </main>
    </div>
  )
}
