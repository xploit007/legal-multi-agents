import React, { useState } from 'react'

// Agent color configurations - Suits-inspired names
const AGENT_COLORS = {
  'Harvey': {
    bg: 'bg-blue-50',
    border: 'border-blue-300',
    header: 'bg-blue-600',
    text: 'text-blue-700',
    icon: 'text-blue-600',
    thinking: 'bg-blue-100'
  },
  'Louis': {
    bg: 'bg-purple-50',
    border: 'border-purple-300',
    header: 'bg-purple-600',
    text: 'text-purple-700',
    icon: 'text-purple-600',
    thinking: 'bg-purple-100'
  },
  'Tanner': {
    bg: 'bg-red-50',
    border: 'border-red-300',
    header: 'bg-red-600',
    text: 'text-red-700',
    icon: 'text-red-600',
    thinking: 'bg-red-100'
  },
  'Jessica': {
    bg: 'bg-green-50',
    border: 'border-green-300',
    header: 'bg-green-600',
    text: 'text-green-700',
    icon: 'text-green-600',
    thinking: 'bg-green-100'
  }
}

// Agent icons
const AGENT_ICONS = {
  'Harvey': (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  'Louis': (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
    </svg>
  ),
  'Tanner': (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  'Jessica': (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

// Agent descriptions - Suits character roles
const AGENT_DESCRIPTIONS = {
  'Harvey': 'Lead Trial Strategist - "The Closer"',
  'Louis': 'Precedent Expert - "The Savant"',
  'Tanner': 'Adversarial Counsel - "The Destroyer"',
  'Jessica': 'Managing Partner - "The Mediator"'
}

function AgentPanel({ agentName, status, content, role }) {
  const [isExpanded, setIsExpanded] = useState(true)
  const colors = AGENT_COLORS[agentName] || AGENT_COLORS['Harvey']
  const icon = AGENT_ICONS[agentName]
  const description = AGENT_DESCRIPTIONS[agentName] || role

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

    // Split by double newlines for paragraphs
    const paragraphs = text.split(/\n\n+/)

    return paragraphs.map((para, idx) => {
      // Check for headers (lines starting with **)
      if (para.startsWith('**') && para.includes('**')) {
        const headerMatch = para.match(/^\*\*(.+?)\*\*(.*)/)
        if (headerMatch) {
          return (
            <div key={idx} className="mb-4">
              <h4 className="font-bold text-gray-800 mb-2">{headerMatch[1]}</h4>
              {headerMatch[2] && <p className="text-gray-700">{headerMatch[2].trim()}</p>}
            </div>
          )
        }
      }

      // Check for numbered headers (like "1. **Header**")
      if (/^\d+\.\s*\*\*/.test(para)) {
        const lines = para.split('\n')
        return (
          <div key={idx} className="mb-4">
            {lines.map((line, lineIdx) => {
              const boldMatch = line.match(/\*\*(.+?)\*\*/)
              if (boldMatch) {
                return (
                  <p key={lineIdx} className="text-gray-700">
                    <strong>{boldMatch[1]}</strong>
                    {line.replace(/\*\*.+?\*\*/, '').trim()}
                  </p>
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
          <ul key={idx} className="list-disc list-inside mb-4 space-y-1">
            {items.map((item, itemIdx) => (
              <li key={itemIdx} className="text-gray-700">
                {item.replace(/^-\s*/, '').replace(/\*\*(.+?)\*\*/g, '$1')}
              </li>
            ))}
          </ul>
        )
      }

      // Regular paragraph
      return (
        <p key={idx} className="text-gray-700 mb-3 leading-relaxed">
          {para.replace(/\*\*(.+?)\*\*/g, '$1')}
        </p>
      )
    })
  }

  return (
    <div className={`agent-card rounded-xl border-2 ${colors.border} ${colors.bg} overflow-hidden shadow-md`}>
      {/* Header */}
      <div className={`${colors.header} px-4 py-3 flex items-center justify-between`}>
        <div className="flex items-center gap-3">
          <div className="text-white opacity-90">
            {icon}
          </div>
          <div>
            <h3 className="font-semibold text-white">{agentName}</h3>
            <p className="text-xs text-white opacity-80">{description}</p>
          </div>
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-2">
          {status === 'waiting' && (
            <span className="px-3 py-1 bg-white/20 text-white text-xs font-medium rounded-full">
              Waiting
            </span>
          )}
          {status === 'thinking' && (
            <span className="px-3 py-1 bg-yellow-400 text-yellow-900 text-xs font-medium rounded-full animate-pulse flex items-center gap-1">
              <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Analyzing
            </span>
          )}
          {status === 'done' && (
            <span className="px-3 py-1 bg-green-400 text-green-900 text-xs font-medium rounded-full flex items-center gap-1">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Complete
            </span>
          )}

          {/* Expand/Collapse for completed */}
          {status === 'done' && content && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-white/80 hover:text-white ml-2"
            >
              <svg
                className={`w-5 h-5 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className={`p-4 ${!isExpanded && status === 'done' ? 'hidden' : ''}`}>
        {status === 'waiting' && (
          <div className={`${colors.thinking} rounded-lg p-6 text-center`}>
            <div className={`${colors.icon} mb-2`}>
              <svg className="w-8 h-8 mx-auto opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className={`text-sm ${colors.text} opacity-60`}>Waiting to begin analysis...</p>
          </div>
        )}

        {status === 'thinking' && (
          <div className={`${colors.thinking} rounded-lg p-6`}>
            <div className="flex items-center justify-center gap-2 mb-3">
              <div className={`w-2 h-2 ${colors.header} rounded-full animate-bounce`} style={{ animationDelay: '0ms' }}></div>
              <div className={`w-2 h-2 ${colors.header} rounded-full animate-bounce`} style={{ animationDelay: '150ms' }}></div>
              <div className={`w-2 h-2 ${colors.header} rounded-full animate-bounce`} style={{ animationDelay: '300ms' }}></div>
            </div>
            <p className={`text-sm ${colors.text} text-center font-medium`}>
              {agentName} is analyzing the case...
            </p>
          </div>
        )}

        {status === 'done' && content && (
          <div className="legal-content text-sm max-h-96 overflow-y-auto pr-2">
            {formatContent(content)}
          </div>
        )}
      </div>
    </div>
  )
}

export default AgentPanel
