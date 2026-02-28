import { useState, useRef, useEffect } from 'react'

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am the customer support assistant for SecureCorp. How can I help you today?' }
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

      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messages: apiMessages }),
      })

      if (!response.ok) {
        throw new Error('Server returned an error')
      }

      const data = await response.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch (error) {
      console.error("Chat error:", error)
      setMessages(prev => [...prev, { 
        role: 'system-error', 
        content: 'Error connecting to the SecureCorp backend. Make sure the FastAPI server is running.' 
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        SecureCorp Assistant
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
            placeholder="Type your message..."
            disabled={isLoading}
            autoComplete="off"
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={!input.trim() || isLoading}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  )
}

export default App
