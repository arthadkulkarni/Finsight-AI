import DOMPurify from 'dompurify'
import { useEffect, useRef } from 'react'
import { resolveImageUrl } from '../api/client'
import type { Source } from '../api/types'

interface SourceCardProps {
  source: Source
  highlighted: boolean
}

export function SourceCard({ source, highlighted }: SourceCardProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (highlighted) {
      ref.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [highlighted])

  return (
    <div
      id={`source-${source.id}`}
      ref={ref}
      className={`source-card${highlighted ? ' source-card--highlighted' : ''}`}
    >
      <div className="source-card__header">
        <span className="source-card__badge">{source.id}</span>
        <span className="source-card__type">{source.element_type}</span>
        <span className="source-card__location">
          {source.document_name}
          {source.page_number != null ? ` · p.${source.page_number}` : ''}
        </span>
      </div>
      {source.section_heading && (
        <div className="source-card__heading">{source.section_heading}</div>
      )}
      <SourceContent source={source} />
    </div>
  )
}

function SourceContent({ source }: { source: Source }) {
  if (source.element_type === 'table' && source.content) {
    // Table HTML comes from parsing an uploaded PDF — sanitize before
    // injecting it, since a crafted PDF could otherwise smuggle
    // script/markup into a table cell.
    const safeHtml = DOMPurify.sanitize(source.content)
    return <div className="source-card__table" dangerouslySetInnerHTML={{ __html: safeHtml }} />
  }

  if (source.element_type === 'chart') {
    const imageSrc = resolveImageUrl(source.image_url)
    return (
      <div className="source-card__chart">
        {imageSrc ? (
          <img src={imageSrc} alt={source.section_heading ?? 'Chart from filing'} />
        ) : (
          <p className="source-card__missing">Chart image unavailable</p>
        )}
        {source.content && <p className="source-card__caption">{source.content}</p>}
      </div>
    )
  }

  return <p className="source-card__text">{source.content}</p>
}
