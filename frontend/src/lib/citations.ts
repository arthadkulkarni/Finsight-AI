export type MessageSegment = { type: 'text'; value: string } | { type: 'citation'; ids: number[] }

const CITATION_GROUP_RE = /(?:\[\d+\])+/g
const SINGLE_CITATION_RE = /\[(\d+)\]/g

/**
 * Splits assistant message text into plain-text and citation-marker
 * segments, so the UI can render "[1][2]" as clickable badges instead of
 * literal brackets. Adjacent markers (e.g. "[1][2]") group into one segment
 * with multiple ids — matches the format the system prompt asks Claude for
 * (backend/app/services/generation.py).
 */
export function splitCitations(text: string): MessageSegment[] {
  const segments: MessageSegment[] = []
  let lastIndex = 0

  for (const match of text.matchAll(CITATION_GROUP_RE)) {
    const start = match.index
    if (start > lastIndex) {
      segments.push({ type: 'text', value: text.slice(lastIndex, start) })
    }
    const ids = [...match[0].matchAll(SINGLE_CITATION_RE)].map((m) => Number(m[1]))
    segments.push({ type: 'citation', ids })
    lastIndex = start + match[0].length
  }

  if (lastIndex < text.length) {
    segments.push({ type: 'text', value: text.slice(lastIndex) })
  }

  return segments
}
