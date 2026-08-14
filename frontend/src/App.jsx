import { useState } from 'react'
import ChatWindow from './components/ChatWindow'
import ChatInput from './components/ChatInput'

const API_URL = import.meta.env.VITE_API_URL || '/chat'

export default function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const handleSend = async (text) => {
    const userMsg = { role: 'user', content: text }
    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)
    setLoading(true)

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: updatedMessages }),
      })

      if (!res.ok) {
        let msg = `HTTP ${res.status}`
        try {
          const err = await res.json()
          msg = err.detail || msg
        } catch {
          const text = await res.text()
          if (text) msg = text.slice(0, 200)
        }
        throw new Error(msg)
      }

      const data = await res.json()
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.reply, sources: data.sources },
      ])
    } catch (err) {
      const msg = err.message === 'Failed to fetch'
        ? 'Cannot reach the backend. Please try again later.'
        : err.message
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${msg}`, sources: [] },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-ghana-green">
      <header className="flex items-center gap-3 px-5 py-4 bg-ghana-green border-b-4 border-ghana-gold shadow-lg">
        <span className="text-3xl">🇬🇭</span>
        <div>
          <h1 className="text-lg font-bold leading-tight text-ghana-gold">CreativeArts</h1>
          <p className="text-xs text-white font-medium">Ask about music, film, fashion, arts & more</p>
        </div>
      </header>

      <ChatWindow messages={messages} loading={loading} />
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  )
}
