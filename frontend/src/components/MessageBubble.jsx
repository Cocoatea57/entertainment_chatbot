import Markdown from 'react-markdown'
import SourceIndicator from './SourceIndicator'

export default function MessageBubble({ role, content, sources }) {
  const isUser = role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className="max-w-[75%]">
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-ghana-gold text-ghana-black rounded-br-md font-medium'
              : 'bg-ghana-green text-white rounded-bl-md'
          }`}
        >
          {isUser ? (
            <span className="whitespace-pre-wrap">{content}</span>
          ) : (
            <div className="prose-chat">
              <Markdown remarkPlugins={[]}>{content}</Markdown>
            </div>
          )}
        </div>

        {!isUser && <SourceIndicator sources={sources} />}
      </div>
    </div>
  )
}
