import { useEffect } from 'react'
import { ChatWindow } from './ChatWindow'
import { UploadPanel } from './UploadPanel'

export function ChatPage() {
  useEffect(() => {
    // Without this, dropping a file anywhere on the page outside the exact
    // upload dropzone falls through to the browser's native default for
    // drop events — navigating the tab to open the file directly — instead
    // of being a harmless no-op. Only the dropzone itself should react to
    // a drop; everywhere else should just swallow it.
    const preventDefault = (event: DragEvent) => event.preventDefault()
    window.addEventListener('dragover', preventDefault)
    window.addEventListener('drop', preventDefault)
    return () => {
      window.removeEventListener('dragover', preventDefault)
      window.removeEventListener('drop', preventDefault)
    }
  }, [])

  return (
    <div className="chat-page">
      <header className="chat-page__header">
        <h1>FinSight AI</h1>
        <p>Ask questions about SEC 10-K filings, with cited answers.</p>
      </header>
      <div className="chat-page__body">
        <aside className="chat-page__sidebar">
          <UploadPanel />
        </aside>
        <main className="chat-page__main">
          <ChatWindow />
        </main>
      </div>
    </div>
  )
}
