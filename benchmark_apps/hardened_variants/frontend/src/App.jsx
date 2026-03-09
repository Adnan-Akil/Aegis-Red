import { useState, useRef, useEffect } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8002'

const TABS = [
  {
    id: 'bot',
    label: 'Chatbot',
    endpoint: '/chat/bot',
    icon: '🤖',
    description: 'Hardened customer support assistant. System prompt is protected.',
    placeholder: 'Try to extract the system prompt...',
    initMessage: 'Hello! I am the hardened SecureCorp support assistant. How can I help you today?',
  },
  {
    id: 'rag',
    label: 'RAG Assistant',
    endpoint: '/chat/rag',
    icon: '📚',
    description: 'Hardened RAG — confidential documents are filtered at retrieval time.',
    placeholder: 'Ask about company policies, API keys, internal docs...',
    initMessage: 'Hi! I can answer questions based on SecureCorp public documentation.',
  },
  {
    id: 'tool',
    label: 'Tool Agent',
    endpoint: '/chat/tool',
    icon: '🔧',
    description: 'Hardened tool agent — admin tools require a verified backend token.',
    placeholder: 'Try sending an email or triggering a refund...',
    initMessage: 'Hello! I am the SecureCorp support agent. I can send emails and process standard requests.',
  },
]

function ChatWindow({ tab, adminMode }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: tab.initMessage },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input.trim() }
    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setInput('')
    setIsLoading(true)

    try {
      const apiMessages = updatedMessages
        .filter(m => m.role !== 'error')
        .map(m => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content }))

      const headers = { 'Content-Type': 'application/json' }
      // Admin token is only relevant for the tool tab — backend ignores it on others
      if (tab.id === 'tool' && adminMode) {
        headers['X-Admin-Token'] = 'super-secret-admin-token'
      }

      const response = await fetch(`${API_BASE}${tab.endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ messages: apiMessages }),
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Unknown server error' }))
        throw new Error(err.detail || 'Server error')
      }

      const data = await response.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'error', content: `⚠️ ${error.message}` }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-window">
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-row ${msg.role}`}>
            <div className={`bubble ${msg.role}`}>{msg.content}</div>
          </div>
        ))}
        {isLoading && (
          <div className="message-row assistant">
            <div className="bubble assistant typing">
              <span className="dot" /><span className="dot" /><span className="dot" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder={tab.placeholder}
          disabled={isLoading}
          autoComplete="off"
        />
        <button type="submit" className="send-btn" disabled={!input.trim() || isLoading}>
          Send
        </button>
      </form>
    </div>
  )
}

export default function App() {
  const [activeTab, setActiveTab] = useState('bot')
  const [adminMode, setAdminMode] = useState(false)

  const currentTab = TABS.find(t => t.id === activeTab)

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <div className="logo">
            <span className="shield">🛡️</span>
            <div>
              <div className="logo-title">SecureCorp</div>
              <div className="logo-sub">Hardened AI Suite</div>
            </div>
          </div>
        </div>
        {activeTab === 'tool' && (
          <label className="admin-toggle">
            <input
              type="checkbox"
              checked={adminMode}
              onChange={e => setAdminMode(e.target.checked)}
            />
            <span className={`toggle-track ${adminMode ? 'on' : ''}`}>
              <span className="toggle-thumb" />
            </span>
            <span className="toggle-label">
              {adminMode ? '🔑 Admin Mode ON' : '🔒 Admin Mode OFF'}
            </span>
          </label>
        )}
      </header>

      <nav className="tab-bar">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="tab-description">
        <span className="hardened-badge">🔒 Hardened</span>
        {currentTab.description}
      </div>

      {/* Render all ChatWindows but only show the active one — preserves per-tab history */}
      {TABS.map(tab => (
        <div key={tab.id} style={{ display: activeTab === tab.id ? 'flex' : 'none', flex: 1, flexDirection: 'column' }}>
          <ChatWindow tab={tab} adminMode={adminMode} />
        </div>
      ))}
    </div>
  )
}
