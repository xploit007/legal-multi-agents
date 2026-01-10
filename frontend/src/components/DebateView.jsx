import React from 'react'
import AgentPanel from './AgentPanel'

function DebateView({ agents }) {
  // Suits-inspired agent order
  const agentOrder = ['Harvey', 'Louis', 'Tanner', 'Jessica']

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Legal Council</h2>
          <p className="text-sm text-gray-500">Your team of AI legal experts</p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-gray-300 rounded-full"></span>
            <span className="text-gray-600">Waiting</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></span>
            <span className="text-gray-600">Analyzing</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            <span className="text-gray-600">Complete</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {agentOrder.map((agentName) => {
          const agent = agents[agentName] || { status: 'waiting', content: null }
          return (
            <AgentPanel
              key={agentName}
              agentName={agentName}
              status={agent.status}
              content={agent.content}
              role={agent.role}
            />
          )
        })}
      </div>
    </div>
  )
}

export default DebateView
