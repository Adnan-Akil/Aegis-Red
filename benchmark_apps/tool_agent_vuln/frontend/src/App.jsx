import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am the SecureCorp Automated Action Agent. I can help you send emails to customers or process other standard requests.' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input.trim() }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Create the messages array for the API (filtering out error messages if any)
      const apiMessages = [...messages, userMessage]
        .filter(msg => msg.role !== 'system-error')
        .map(msg => ({ role: msg.role === 'assistant' ? 'assistant' : 'user', content: msg.content }))

      // Connecting to the Tool Agent backend on port 8003
      const response = await fetch('http://localhost:8003/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messages: apiMessages }),
      })

      if (!response.ok) {
        let errorMsg = 'Server returned an error';
        try {
          const errorData = await response.json();
          errorMsg = `Error ${response.status}: ${errorData.detail || errorData.message || JSON.stringify(errorData)}`;
        } catch(e) {
          errorMsg = `HTTP Error ${response.status}`;
        }
        throw new Error(errorMsg)
      }

      const data = await response.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch (error) {
      console.error("Chat error:", error)
      setMessages(prev => [...prev, { 
        role: 'system-error', 
        content: `⚠️ ${error.message}` 
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        SecureCorp Automated Action Agent
      </header>
      
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-wrapper ${msg.role === 'assistant' ? 'bot' : msg.role}`}>
            <div className={`message ${msg.role === 'assistant' ? 'bot' : msg.role}`}>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-wrapper bot">
            <div className="typing-indicator">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <form className="chat-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your command..."
            disabled={isLoading}
            autoComplete="off"
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={!input.trim() || isLoading}
          >
            Execute
          </button>
        </form>
      </div>
    </div>
  )
}

export default App
