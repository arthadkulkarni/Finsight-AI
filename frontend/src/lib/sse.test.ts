import { describe, expect, it } from 'vitest'
import { parseSSEStream } from './sse'

function streamFromChunks(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  let index = 0
  return new ReadableStream({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(encoder.encode(chunks[index]))
        index += 1
      } else {
        controller.close()
      }
    },
  })
}

async function collect<T>(stream: ReadableStream<Uint8Array>): Promise<T[]> {
  const events: T[] = []
  for await (const event of parseSSEStream<T>(stream)) {
    events.push(event)
  }
  return events
}

describe('parseSSEStream', () => {
  it('parses a single event delivered in one chunk', async () => {
    const events = await collect(streamFromChunks(['data: {"type":"done"}\n\n']))
    expect(events).toEqual([{ type: 'done' }])
  })

  it('parses multiple events across multiple reads', async () => {
    const events = await collect(
      streamFromChunks(['data: {"type":"delta","text":"hi"}\n\n', 'data: {"type":"done"}\n\n'])
    )
    expect(events).toEqual([{ type: 'delta', text: 'hi' }, { type: 'done' }])
  })

  it('reassembles an event split across a chunk boundary', async () => {
    const events = await collect(
      streamFromChunks(['data: {"typ', 'e":"done"}', '\n\n'])
    )
    expect(events).toEqual([{ type: 'done' }])
  })

  it('skips comment/keep-alive lines with no data field', async () => {
    const events = await collect(
      streamFromChunks([': keep-alive\n\n', 'data: {"type":"done"}\n\n'])
    )
    expect(events).toEqual([{ type: 'done' }])
  })

  it('skips a frame with invalid JSON instead of throwing', async () => {
    const events = await collect(
      streamFromChunks(['data: not-json\n\n', 'data: {"type":"done"}\n\n'])
    )
    expect(events).toEqual([{ type: 'done' }])
  })

  it('yields nothing for an empty stream', async () => {
    const events = await collect(streamFromChunks([]))
    expect(events).toEqual([])
  })
})
