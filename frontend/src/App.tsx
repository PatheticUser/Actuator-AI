import { useState, useEffect, useRef } from 'react'
import { marked } from 'marked'
import * as api from './api'
import './App.css'

function App() {
  const [agents, setAgents] = useState<api.Agent[]>([])
  const [messages, setMessages] = useState<api.Message[]>([])
  const [inputText, setInputText] = useState('')
  const [email] = useState(() => localStorage.getItem('user_email') || 'demo@user.com')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)


  useEffect(() => {
    api.fetchAgents().then(setAgents).catch(console.error)
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return

    const userMsg: api.Message = { role: 'user', content: inputText }
    setMessages(prev => [...prev, userMsg])
    setInputText('')
    setIsLoading(true)

    try {
      const res = await api.sendMessage(inputText, email, conversationId || undefined)
      if (res.conversation_id) setConversationId(res.conversation_id)
      
      const aiMsg: api.Message = {
        role: 'assistant',
        content: res.response,
        agent_name: res.agent_name
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, { role: 'assistant', content: 'Connection error. Check backend.' }])
    } finally {
      setIsLoading(false)
    }
  }

  const resetSession = () => {
    setMessages([])
    setConversationId(null)
  }

  const renderContent = (content: string) => {
    return { __html: marked.parse(content) }
  }

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="brand" onClick={resetSession} title="Reset Session">Actuator</div>
          
          <div className="agent-status-panel">
            <label>System Specialists</label>
            <div className="agent-chips">
              {agents.map(agent => (
                <div key={agent.key} className="chip">
                  <span className="dot"></span>
                  {agent.name.split(' ')[0]}
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <button className="new-session-btn" onClick={resetSession}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          New Conversation
        </button>
      </aside>


      <main className="chat-main">
        <div className="chat-viewport">
          {messages.length === 0 && (
            <div className="welcome">
              <div className="welcome-icon">⚡</div>
              <h1>Systems Primed.</h1>
              <p>How can we assist your workflow today?</p>
            </div>
          )}
          
          {messages.map((msg, i) => (
            <div key={i} className={`msg-group ${msg.role}`}>
              <div className="msg-bubble">
                {msg.role === 'assistant' && (
                  <span className="agent-label">{msg.agent_name}</span>
                )}
                <div 
                  className="markdown-body" 
                  dangerouslySetInnerHTML={renderContent(msg.content)} 
                />
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="msg-group assistant">
              <div className="msg-bubble loading-bubble">
                <div className="typing-loader"><span></span><span></span><span></span></div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="input-area">
          <div className="input-container">
            <textarea 
              placeholder="Start typing..." 
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              rows={1}
            />
            <button className="send-btn" onClick={handleSend} disabled={isLoading || !inputText.trim()}>
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
