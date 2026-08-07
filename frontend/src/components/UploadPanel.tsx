import { useCallback, useRef, useState, type DragEvent } from 'react'
import { getUploadStatus, uploadDocument } from '../api/client'
import type { IngestResult } from '../api/types'

type UploadStatus = 'uploading' | 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE'

interface UploadItem {
  id: string
  filename: string
  status: UploadStatus
  result?: IngestResult
  error?: string
}

let uploadCounter = 0
function nextUploadId(): string {
  uploadCounter += 1
  return `upload-${uploadCounter}`
}

const POLL_INTERVAL_MS = 3000

export function UploadPanel() {
  const [uploads, setUploads] = useState<UploadItem[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function updateUpload(id: string, patch: Partial<UploadItem>) {
    setUploads((prev) => prev.map((u) => (u.id === id ? { ...u, ...patch } : u)))
  }

  function pollStatus(localId: string, taskId: string) {
    const poll = async () => {
      try {
        const status = await getUploadStatus(taskId)
        if (status.status === 'SUCCESS') {
          updateUpload(localId, { status: 'SUCCESS', result: status.result })
          return
        }
        if (status.status === 'FAILURE') {
          updateUpload(localId, { status: 'FAILURE', error: status.error })
          return
        }
        updateUpload(localId, { status: status.status as UploadStatus })
      } catch {
        // Transient network hiccup while polling — just try again.
      }
      setTimeout(poll, POLL_INTERVAL_MS)
    }
    void poll()
  }

  async function uploadOne(file: File) {
    const localId = nextUploadId()
    setUploads((prev) => [...prev, { id: localId, filename: file.name, status: 'uploading' }])

    try {
      const { task_id: taskId } = await uploadDocument(file)
      updateUpload(localId, { status: 'PENDING' })
      pollStatus(localId, taskId)
    } catch (err) {
      updateUpload(localId, {
        status: 'FAILURE',
        error: err instanceof Error ? err.message : 'Upload failed.',
      })
    }
  }

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return
    for (const file of Array.from(files)) {
      if (!file.name.toLowerCase().endsWith('.pdf')) continue
      void uploadOne(file)
    }
  }, [])

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragging(false)
    handleFiles(event.dataTransfer.files)
  }

  return (
    <div className="upload-panel">
      <div
        className={`upload-panel__dropzone${isDragging ? ' upload-panel__dropzone--active' : ''}`}
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
      >
        <p>Drag a 10-K PDF here, or click to browse</p>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          hidden
          onChange={(event) => handleFiles(event.target.files)}
        />
      </div>

      <ul className="upload-panel__list">
        {uploads.map((upload) => (
          <li key={upload.id} className="upload-item">
            <span className="upload-item__name">{upload.filename}</span>
            <UploadStatusBadge upload={upload} />
          </li>
        ))}
      </ul>
    </div>
  )
}

function UploadStatusBadge({ upload }: { upload: UploadItem }) {
  if (upload.status === 'SUCCESS' && upload.result) {
    return (
      <span className="upload-item__status upload-item__status--success">
        Ready — {upload.result.num_text_chunks} text, {upload.result.num_tables} tables,{' '}
        {upload.result.num_charts} charts
      </span>
    )
  }
  if (upload.status === 'FAILURE') {
    return (
      <span className="upload-item__status upload-item__status--failure">
        {upload.error ?? 'Failed'}
      </span>
    )
  }
  return <span className="upload-item__status upload-item__status--pending">Processing…</span>
}
