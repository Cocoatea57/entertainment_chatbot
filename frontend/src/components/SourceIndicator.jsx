import { useState } from 'react'

export default function SourceIndicator({ sources }) {
  const [open, setOpen] = useState(false)

  if (!sources || sources.length === 0) return null

  return (
    <div className="relative inline-block mt-1.5">
      <button
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-1 text-[10px] text-black hover:text-green-500 transition-colors cursor-pointer"
      >
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {sources.length} source{sources.length > 1 ? 's' : ''}
      </button>

      {open && (
        <div
          onMouseEnter={() => setOpen(true)}
          onMouseLeave={() => setOpen(false)}
          className="absolute bottom-full left-0 mb-2 w-80 bg-white rounded-xl shadow-2xl border border-gray-200 p-3 z-50"
        >
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">
            RAG Sources
          </p>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {sources.map((src, i) => (
              <div key={i} className="border-b border-gray-100 pb-2 last:border-0 last:pb-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-bold text-ghana-green bg-ghana-green/10 px-1.5 py-0.5 rounded">
                    {src.category}
                  </span>
                  <span className="text-[10px] text-black">
                    {src.topic}
                  </span>
                  <span className="ml-auto text-[10px] text-ghana-green font-medium">
                    {Math.round(src.relevance * 100)}%
                  </span>
                </div>
                <p className="text-[11px] text-gray-600 leading-relaxed">
                  {src.text}...
                </p>
              </div>
            ))}
          </div>
          <div className="absolute bottom-0 left-4 w-2 h-2 bg-white border-r border-b border-gray-200 transform translate-y-1/2 rotate-45" />
        </div>
      )}
    </div>
  )
}
