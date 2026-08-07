import { parseSSEStream } from '../lib/sse'
import type { ChatEvent, StatusResponse, UploadResponse } from './types'

// Both `npm run dev` (via vite.config.ts's proxy) and the Docker Compose
// stack (via frontend/nginx.conf) route /api/* to the backend — the app
// never needs to know the backend's real host.
const API_BASE = '/api'

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response))
  }
  return (await response.json()) as UploadResponse
}

export async function getUploadStatus(taskId: string): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE}/documents/status/${taskId}`)
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response))
  }
  return (await response.json()) as StatusResponse
}

export async function* streamChat(question: string): AsyncGenerator<ChatEvent> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  if (!response.ok || !response.body) {
    throw new Error(await extractErrorMessage(response))
  }
  yield* parseSSEStream<ChatEvent>(response.body)
}

export function resolveImageUrl(imageUrl: string | null): string | null {
  return imageUrl ? `${API_BASE}${imageUrl}` : null
}

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') return body.detail
  } catch {
    // Response wasn't JSON — fall through to the generic message below.
  }
  return `Request failed with status ${response.status}`
}
