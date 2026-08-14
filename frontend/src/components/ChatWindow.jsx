import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'

export default function ChatWindow({ messages, loading }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-1 bg-white/95">
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-6xl mb-4">🇬🇭</div>
            <p className="text-lg font-bold text-ghana-green">CreativeArts</p>
            <p className="text-sm mt-2 text-gray-500">Ask me about music, film, fashion, arts, and more</p>
          </div>
        </div>
      )}

      {messages.map((msg, i) => (
        <MessageBubble
          key={i}
          role={msg.role}
          content={msg.content}
          sources={msg.sources}
        />
      ))}

      {loading && (
        <div className="flex justify-start mb-4">
          <div className="bg-ghana-green/10 border border-ghana-green/20 text-ghana-green px-4 py-3 rounded-2xl rounded-bl-md text-sm">
            <span className="inline-flex gap-1">
              <span className="w-2 h-2 bg-ghana-green rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-ghana-green rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-ghana-green rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
