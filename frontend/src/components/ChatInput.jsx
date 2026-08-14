import { useState } from 'react'

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 p-4 border-t-4 border-ghana-gold bg-ghana-green">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask about Ghana's creative industry..."
        disabled={disabled}
        className="flex-1 px-4 py-3 rounded-xl border-2 border-ghana-gold bg-white text-ghana-black placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-ghana-gold/50 text-sm disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="px-6 py-3 bg-ghana-gold text-ghana-black rounded-xl font-bold hover:bg-yellow-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
      >
        Send
      </button>
    </form>
  )
}
