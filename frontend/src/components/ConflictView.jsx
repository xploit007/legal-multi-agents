import React from 'react'

function ConflictView({ conflicts }) {
  if (!conflicts || conflicts.length === 0) {
    return null
  }

  return (
    <div className="mt-8">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-amber-100 rounded-lg">
          <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-800">Detected Conflicts</h2>
          <p className="text-sm text-gray-500">Disagreements identified between agents</p>
        </div>
      </div>

      <div className="space-y-4">
        {conflicts.map((conflict, index) => (
          <div
            key={conflict.conflict_id || index}
            className="conflict-card bg-amber-50 border border-amber-200 rounded-xl p-5 shadow-sm"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-amber-200 text-amber-800 text-xs font-semibold rounded-full">
                  Conflict #{index + 1}
                </span>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  conflict.status === 'resolved'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-700'
                }`}>
                  {conflict.status === 'resolved' ? 'Resolved' : 'Unresolved'}
                </span>
              </div>
            </div>

            <h3 className="font-semibold text-gray-800 mb-2">{conflict.issue}</h3>

            <div className="mb-3">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Agents Involved:
              </span>
              <div className="flex flex-wrap gap-2 mt-1">
                {(conflict.agents_involved || []).map((agent, agentIdx) => (
                  <span
                    key={agentIdx}
                    className={`px-2 py-1 text-xs font-medium rounded-full ${
                      agent === 'Lead Strategist' ? 'bg-blue-100 text-blue-700' :
                      agent === 'Precedent Expert' ? 'bg-purple-100 text-purple-700' :
                      agent === 'Adversarial Counsel' ? 'bg-red-100 text-red-700' :
                      'bg-green-100 text-green-700'
                    }`}
                  >
                    {agent}
                  </span>
                ))}
              </div>
            </div>

            <div className="bg-white/60 rounded-lg p-3">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">
                Description:
              </span>
              <p className="text-sm text-gray-700 leading-relaxed">
                {conflict.description}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-4 p-4 bg-amber-100/50 rounded-lg border border-amber-200">
        <p className="text-sm text-amber-800">
          <strong>{conflicts.length} conflict{conflicts.length !== 1 ? 's' : ''}</strong> detected.
          The Moderator will consider these disagreements when synthesizing the final strategy.
        </p>
      </div>
    </div>
  )
}

export default ConflictView
