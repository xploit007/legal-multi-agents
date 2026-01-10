import React, { useState } from 'react'

function FinalStrategy({ strategy }) {
  const [showRejected, setShowRejected] = useState(false)

  if (!strategy) {
    return null
  }

  // Format content with basic markdown-like parsing
  const formatContent = (text) => {
    if (!text) return null

    // Handle case where text is an object with content property
    if (typeof text === 'object') {
      text = text.content || JSON.stringify(text)
    }

    // Ensure text is a string
    if (typeof text !== 'string') {
      text = String(text)
    }

    const paragraphs = text.split(/\n\n+/)

    return paragraphs.map((para, idx) => {
      // Check for headers with **
      if (para.match(/^\*\*\d*\.?\s*.+?\*\*/)) {
        const lines = para.split('\n')
        return (
          <div key={idx} className="mb-4">
            {lines.map((line, lineIdx) => {
              const headerMatch = line.match(/^\*\*(.+?)\*\*(.*)/)
              if (headerMatch) {
                return (
                  <div key={lineIdx}>
                    <h4 className="font-bold text-gray-800 text-lg mb-2">{headerMatch[1]}</h4>
                    {headerMatch[2] && <p className="text-gray-700">{headerMatch[2].trim()}</p>}
                  </div>
                )
              }
              return <p key={lineIdx} className="text-gray-700">{line}</p>
            })}
          </div>
        )
      }

      // Handle bullet points
      if (para.includes('\n-') || para.startsWith('-')) {
        const items = para.split('\n').filter(item => item.trim())
        return (
          <ul key={idx} className="list-disc list-inside mb-4 space-y-2">
            {items.map((item, itemIdx) => (
              <li key={itemIdx} className="text-gray-700">
                {item.replace(/^-\s*/, '').replace(/\*\*(.+?)\*\*/g, '$1')}
              </li>
            ))}
          </ul>
        )
      }

      // Handle numbered lists
      if (para.match(/^\d+\./)) {
        const items = para.split('\n').filter(item => item.trim())
        return (
          <ol key={idx} className="list-decimal list-inside mb-4 space-y-2">
            {items.map((item, itemIdx) => (
              <li key={itemIdx} className="text-gray-700">
                {item.replace(/^\d+\.\s*/, '').replace(/\*\*(.+?)\*\*/g, '$1')}
              </li>
            ))}
          </ol>
        )
      }

      // Regular paragraph
      return (
        <p key={idx} className="text-gray-700 mb-4 leading-relaxed">
          {para.replace(/\*\*(.+?)\*\*/g, '$1')}
        </p>
      )
    })
  }

  return (
    <div className="mt-8">
      {/* Success Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-green-100 rounded-lg">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Final Strategy</h2>
          <p className="text-sm text-gray-500">Synthesized by the Moderator after reviewing all inputs</p>
        </div>
      </div>

      {/* Main Strategy Card */}
      <div className="strategy-card bg-green-50 border-2 border-green-200 rounded-xl overflow-hidden shadow-lg">
        {/* Header */}
        <div className="bg-green-600 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-white font-semibold">Strategy v{strategy.version || 1}</span>
            </div>
            <span className="px-3 py-1 bg-green-500 text-white text-sm font-medium rounded-full">
              Final Recommendation
            </span>
          </div>
        </div>

        {/* Strategy Content */}
        <div className="p-6">
          <div className="legal-content prose prose-green max-w-none">
            {formatContent(strategy.final_strategy)}
          </div>
        </div>

        {/* Rationale Section */}
        {strategy.rationale && (
          <div className="border-t border-green-200 bg-green-100/50 px-6 py-4">
            <h4 className="font-semibold text-green-800 mb-2 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Synthesis Rationale
            </h4>
            <div className="text-sm text-green-700">
              {typeof strategy.rationale === 'string' ? (
                <p>{strategy.rationale}</p>
              ) : (
                <ul className="space-y-1">
                  <li><strong>Method:</strong> {strategy.rationale.method}</li>
                  <li><strong>Deliberation Rounds:</strong> {strategy.rationale.deliberation_rounds}</li>
                  {strategy.rationale.inputs_considered && (
                    <li>
                      <strong>Inputs:</strong> {strategy.rationale.inputs_considered.arguments} arguments, {strategy.rationale.inputs_considered.counterarguments} counterarguments, {strategy.rationale.inputs_considered.conflicts_resolved} conflicts resolved
                    </li>
                  )}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Rejected Alternatives Section */}
      {strategy.rejected_alternatives && strategy.rejected_alternatives.length > 0 && (
        <div className="mt-6">
          <button
            onClick={() => setShowRejected(!showRejected)}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            <svg
              className={`w-5 h-5 transform transition-transform ${showRejected ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
            <span className="font-medium">
              {showRejected ? 'Hide' : 'Show'} Rejected Alternatives ({strategy.rejected_alternatives.length})
            </span>
          </button>

          {showRejected && (
            <div className="mt-4 bg-gray-50 border border-gray-200 rounded-xl p-5">
              <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
                Alternatives Considered but Rejected
              </h4>
              <ul className="space-y-3">
                {strategy.rejected_alternatives.map((alt, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-6 h-6 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-xs font-bold">
                      {idx + 1}
                    </span>
                    <p className="text-sm text-gray-600">{alt}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="mt-8 flex flex-wrap gap-4 justify-center">
        <button
          onClick={() => window.print()}
          className="px-6 py-3 bg-legal-primary text-white font-medium rounded-lg hover:bg-legal-secondary transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          Print Strategy
        </button>
        <button
          onClick={() => {
            let text = strategy.final_strategy
            if (typeof text === 'object') text = text.content || JSON.stringify(text)
            navigator.clipboard.writeText(text || '')
            alert('Strategy copied to clipboard!')
          }}
          className="px-6 py-3 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Copy to Clipboard
        </button>
      </div>
    </div>
  )
}

export default FinalStrategy
