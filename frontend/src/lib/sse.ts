/**
 * Parses a `text/event-stream` response body into typed events.
 *
 * This implements only the subset of the SSE spec our backend actually
 * uses — one `data: <json>` line per event, separated by a blank line — not
 * `event:`/`id:`/reconnect fields. Browsers can't use the native
 * `EventSource` here anyway, since it only supports GET with no body, and
 * /chat is a POST.
 */
export async function* parseSSEStream<T>(body: ReadableStream<Uint8Array>): AsyncGenerator<T> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let separatorIndex = buffer.indexOf('\n\n')
      while (separatorIndex !== -1) {
        const rawEvent = buffer.slice(0, separatorIndex)
        buffer = buffer.slice(separatorIndex + 2)
        const event = parseEvent<T>(rawEvent)
        if (event !== undefined) yield event
        separatorIndex = buffer.indexOf('\n\n')
      }
    }
  } finally {
    reader.releaseLock()
  }
}

function parseEvent<T>(rawEvent: string): T | undefined {
  const dataLines = rawEvent
    .split('\n')
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice('data:'.length).trimStart())

  if (dataLines.length === 0) return undefined // e.g. an SSE comment/keep-alive line

  try {
    return JSON.parse(dataLines.join('\n')) as T
  } catch {
    return undefined
  }
}
