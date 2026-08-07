export type ElementType = 'text' | 'table' | 'chart'

export interface Source {
  id: number
  element_type: ElementType
  document_name: string
  page_number: number | null
  section_heading: string | null
  content: string | null
  image_url: string | null
  relevance_score: number
}

// Matches the SSE events yielded by backend/app/routers/chat.py
export type ChatEvent =
  | { type: 'delta'; text: string }
  | { type: 'sources'; sources: Source[] }
  | { type: 'done' }
  | { type: 'error'; message: string }

export interface UploadResponse {
  task_id: string
  status: string
  document_name: string
}

export interface IngestResult {
  document_name: string
  num_text_chunks: number
  num_tables: number
  num_charts: number
}

export interface StatusResponse {
  task_id: string
  status: string
  result?: IngestResult
  error?: string
}
