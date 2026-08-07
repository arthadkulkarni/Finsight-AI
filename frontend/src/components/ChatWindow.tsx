import { useEffect, useRef, useState, type FormEvent } from 'react'
import { streamChat } from '../api/client'
import type { Source } from '../api/types'
import { MessageBubble } from './MessageBubble'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  status: 'streaming' | 'done' | 'error'
  sources?: Source[]
  error?: string
}

let messageCounter = 0
function nextMessageId(): string {
  messageCounter += 1
  return `msg-${messageCounter}`
}

export function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [question, setQuestion] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  function updateMessage(id: string, patch: Partial<ChatMessage>) {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch } : m)))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || isStreaming) return

    const assistantId = nextMessageId()
    setMessages((prev) => [
      ...prev,
      { id: nextMessageId(), role: 'user', text: trimmed, status: 'done' },
      { id: assistantId, role: 'assistant', text: '', status: 'streaming' },
    ])
    setQuestion('')
    setIsStreaming(true)

    try {
      for await (const chatEvent of streamChat(trimmed)) {
        if (chatEvent.type === 'delta') {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, text: m.text + chatEvent.text } : m))
          )
        } else if (chatEvent.type === 'sources') {
          updateMessage(assistantId, { sources: chatEvent.sources })
        } else if (chatEvent.type === 'error') {
          updateMessage(assistantId, { status: 'error', error: chatEvent.message })
        }
      }
      updateMessage(assistantId, { status: 'done' })
    } catch (err) {
      updateMessage(assistantId, {
        status: 'error',
        error: err instanceof Error ? err.message : 'Something went wrong.',
      })
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <div className="chat-window">
      <div className="chat-window__messages" ref={scrollRef}>
        {messages.length === 0 && (
          <p className="chat-window__empty">Upload a 10-K and ask a question about it.</p>
        )}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </div>
      <form className="chat-window__input" onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about the filing..."
          disabled={isStreaming}
        />
        <button type="submit" disabled={isStreaming || !question.trim()}>
          {isStreaming ? 'Thinking…' : 'Ask'}
        </button>
      </form>
    </div>
  )
}
