import { useState } from 'react'
import { splitCitations } from '../lib/citations'
import { SourceCard } from './SourceCard'
import type { ChatMessage } from './ChatWindow'

interface MessageBubbleProps {
  message: ChatMessage
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [highlightedId, setHighlightedId] = useState<number | null>(null)

  if (message.role === 'user') {
    return (
      <div className="message message--user">
        <div className="message__bubble">{message.text}</div>
      </div>
    )
  }

  const segments = splitCitations(message.text)

  return (
    <div className="message message--assistant">
      <div className="message__bubble">
        {segments.map((segment, index) =>
          segment.type === 'text' ? (
            <span key={index}>{segment.value}</span>
          ) : (
            <button
              key={index}
              type="button"
              className="citation-badge"
              onClick={() => setHighlightedId(segment.ids[0] ?? null)}
            >
              {segment.ids.join(',')}
            </button>
          )
        )}
        {message.status === 'streaming' && (
          <span className="message__cursor" aria-hidden="true" />
        )}
      </div>
      {message.status === 'error' && (
        <div className="message__error">{message.error ?? 'Something went wrong.'}</div>
      )}
      {message.sources && message.sources.length > 0 && (
        <div className="source-list">
          {message.sources.map((source) => (
            <SourceCard
              key={source.id}
              source={source}
              highlighted={source.id === highlightedId}
            />
          ))}
        </div>
      )}
    </div>
  )
}
