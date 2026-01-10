import React, { useState, useCallback } from 'react'
import CaseInput from './components/CaseInput'
import DebateView from './components/DebateView'
import ConflictView from './components/ConflictView'
import FinalStrategy from './components/FinalStrategy'

const API_URL = '/api'

// Agent names inspired by TV show "Suits"
const INITIAL_AGENTS = {
  'Harvey': { status: 'waiting', content: null, role: 'Lead Strategist' },
  'Louis': { status: 'waiting', content: null, role: 'Precedent Expert' },
  'Tanner': { status: 'waiting', content: null, role: 'Adversarial Counsel' },
  'Jessica': { status: 'waiting', content: null, role: 'Managing Partner' }
}

function App() {
  const [caseId, setCaseId] = useState(null)
  const [currentPhase, setCurrentPhase] = useState('input') // input, analyzing, complete
  const [agents, setAgents] = useState(INITIAL_AGENTS)
  const [conflicts, setConflicts] = useState([])
  const [strategy, setStrategy] = useState(null)
  const [error, setError] = useState(null)
  const [deliberationRound, setDeliberationRound] = useState(0)
  const [totalRounds, setTotalRounds] = useState(0)

  const resetState = () => {
    setCaseId(null)
    setCurrentPhase('input')
    setAgents(INITIAL_AGENTS)
    setConflicts([])
    setStrategy(null)
    setError(null)
    setDeliberationRound(0)
    setTotalRounds(0)
  }

  const handleCaseSubmit = useCallback(async (caseData) => {
    setError(null)
    setCurrentPhase('analyzing')

    try {
      // Create the case
      const response = await fetch(`${API_URL}/cases`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(caseData)
      })

      if (!response.ok) {
        throw new Error('Failed to create case')
      }

      const result = await response.json()
      setCaseId(result.case_id)

      // Connect to SSE stream
      const eventSource = new EventSource(`${API_URL}/cases/${result.case_id}/stream`)
      console.log('[SSE] Connecting to stream for case:', result.case_id)

      eventSource.onopen = () => {
        console.log('[SSE] Connection opened')
      }

      eventSource.addEventListener('agent_started', (event) => {
        const data = JSON.parse(event.data)
        console.log('[SSE] Agent started:', data.agent, data.phase)
        setAgents(prev => ({
          ...prev,
          [data.agent]: { ...prev[data.agent], status: 'thinking', phase: data.phase }
        }))
      })

      eventSource.addEventListener('agent_completed', (event) => {
        const data = JSON.parse(event.data)
        console.log('[SSE] Agent completed:', data.agent, 'content type:', typeof data.content)
        setAgents(prev => ({
          ...prev,
          [data.agent]: {
            ...prev[data.agent],
            status: 'done',
            content: data.content,
            attackVectors: data.attack_vectors,
            rejectedAlternatives: data.rejected_alternatives,
            round: data.round
          }
        }))
      })

      eventSource.addEventListener('deliberation_round_started', (event) => {
        const data = JSON.parse(event.data)
        setDeliberationRound(data.round)
        setTotalRounds(data.total_rounds)
      })

      eventSource.addEventListener('deliberation_round_completed', (event) => {
        // Round completed
      })

      eventSource.addEventListener('detecting_conflicts', () => {
        // Detecting conflicts state
      })

      eventSource.addEventListener('conflict_detected', (event) => {
        const data = JSON.parse(event.data)
        setConflicts(data.conflicts || [])
      })

      eventSource.addEventListener('strategy_ready', (event) => {
        const data = JSON.parse(event.data)
        setStrategy(data.strategy)
        setCurrentPhase('complete')
        eventSource.close()
      })

      eventSource.addEventListener('error', (event) => {
        if (event.data) {
          const data = JSON.parse(event.data)
          setError(data.message)
        }
        eventSource.close()
      })

      eventSource.onerror = async () => {
        eventSource.close()
        // Try to fetch existing data if SSE fails
        try {
          const caseResponse = await fetch(`${API_URL}/cases/${result.case_id}`)
          if (caseResponse.ok) {
            const caseData = await caseResponse.json()
            // Update agents from existing data
            if (caseData.arguments) {
              caseData.arguments.forEach(arg => {
                setAgents(prev => ({
                  ...prev,
                  [arg.agent]: { ...prev[arg.agent], status: 'done', content: arg.content }
                }))
              })
            }
            if (caseData.strategy) {
              setStrategy(caseData.strategy)
              setCurrentPhase('complete')
            }
            if (caseData.conflicts) {
              setConflicts(caseData.conflicts)
            }
          }
        } catch (e) {
          console.error('Failed to fetch case data:', e)
        }
      }

    } catch (err) {
      setError(err.message)
      setCurrentPhase('input')
    }
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-legal-primary text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Legal Strategy Council</h1>
              <p className="text-blue-200 text-sm mt-1">Multi-Agent Legal Analysis System • Inspired by Suits</p>
            </div>
            {currentPhase !== 'input' && (
              <button
                onClick={resetState}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
              >
                New Case
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <strong>Error:</strong> {error}
          </div>
        )}

        {currentPhase === 'input' && (
          <CaseInput onSubmit={handleCaseSubmit} />
        )}

        {(currentPhase === 'analyzing' || currentPhase === 'complete') && (
          <div className="space-y-8">
            {/* Deliberation Progress */}
            {deliberationRound > 0 && currentPhase === 'analyzing' && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="animate-pulse">
                    <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-amber-800">
                      Deliberation Round {deliberationRound} of {totalRounds}
                    </p>
                    <p className="text-sm text-amber-600">
                      Harvey and Tanner are debating the strategy...
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Agent Debate View */}
            <DebateView agents={agents} />

            {/* Conflicts Section */}
            {conflicts.length > 0 && (
              <ConflictView conflicts={conflicts} />
            )}

            {/* Final Strategy Section */}
            {strategy && (
              <FinalStrategy strategy={strategy} />
            )}

            {/* Loading indicator when still analyzing */}
            {currentPhase === 'analyzing' && !strategy && (
              <div className="text-center py-8">
                <div className="inline-flex items-center px-6 py-3 bg-blue-50 rounded-full">
                  <svg className="animate-spin h-5 w-5 text-blue-600 mr-3" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span className="text-blue-700 font-medium">Analysis in progress...</span>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-gray-500 text-sm">
          <p>Legal Strategy Council - MongoDB Hackathon Project</p>
          <p className="mt-1">Powered by Groq Llama 3.3 70B & MongoDB Atlas</p>
        </div>
      </footer>
    </div>
  )
}

export default App
