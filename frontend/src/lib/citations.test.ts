import { describe, expect, it } from 'vitest'
import { splitCitations } from './citations'

describe('splitCitations', () => {
  it('returns a single text segment when there are no citations', () => {
    expect(splitCitations('Net revenue was $0.')).toEqual([
      { type: 'text', value: 'Net revenue was $0.' },
    ])
  })

  it('splits out a single citation marker', () => {
    expect(splitCitations('Net revenue was $0 [1].')).toEqual([
      { type: 'text', value: 'Net revenue was $0 ' },
      { type: 'citation', ids: [1] },
      { type: 'text', value: '.' },
    ])
  })

  it('groups adjacent citation markers into one segment', () => {
    expect(splitCitations('Net loss was $184,644 [1][2].')).toEqual([
      { type: 'text', value: 'Net loss was $184,644 ' },
      { type: 'citation', ids: [1, 2] },
      { type: 'text', value: '.' },
    ])
  })

  it('handles a citation at the very start or end with no surrounding text', () => {
    expect(splitCitations('[1] leads the sentence')).toEqual([
      { type: 'citation', ids: [1] },
      { type: 'text', value: ' leads the sentence' },
    ])
    expect(splitCitations('sentence ends with [3]')).toEqual([
      { type: 'text', value: 'sentence ends with ' },
      { type: 'citation', ids: [3] },
    ])
  })

  it('handles multiple separate citations', () => {
    expect(splitCitations('A [1] and B [2].')).toEqual([
      { type: 'text', value: 'A ' },
      { type: 'citation', ids: [1] },
      { type: 'text', value: ' and B ' },
      { type: 'citation', ids: [2] },
      { type: 'text', value: '.' },
    ])
  })

  it('does not treat non-numeric brackets as citations', () => {
    expect(splitCitations('See [Note 1] for details.')).toEqual([
      { type: 'text', value: 'See [Note 1] for details.' },
    ])
  })
})
