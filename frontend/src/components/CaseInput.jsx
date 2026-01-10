import React, { useState } from 'react'

// Demo case data
const DEMO_CASE = {
  title: "NovaTech Solutions vs. Meridian Ventures",
  facts: `NovaTech Solutions is a 3-year-old AI startup that developed a proprietary machine learning platform for healthcare diagnostics. In March 2024, Meridian Ventures signed a Series A investment agreement promising $5 million in funding over two tranches: Tranche 1 ($2.5M) upon signing (received), and Tranche 2 ($2.5M) upon reaching 50 enterprise customers.

In September 2024, NovaTech reached 53 enterprise customers and notified Meridian to release Tranche 2. Meridian refused, claiming NovaTech's customers were 'trial agreements' not 'enterprise customers', and that the agreement required $100K+ annual contracts.

NovaTech argues the agreement never defined 'enterprise customer' with a revenue minimum, Meridian approved the customer list during due diligence, and a Meridian partner emailed 'Congrats on hitting 50! Let's discuss next steps.'

Due to the funding delay, NovaTech lost two key engineers and a major partnership.`,
  jurisdiction: "Delaware Corporate Law",
  stakes: "$2.5 million + $1.2 million consequential damages"
}

function CaseInput({ onSubmit }) {
  const [formData, setFormData] = useState(DEMO_CASE)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)
    await onSubmit(formData)
    setIsSubmitting(false)
  }

  const handleLoadDemo = () => {
    setFormData(DEMO_CASE)
  }

  const handleClear = () => {
    setFormData({ title: '', facts: '', jurisdiction: '', stakes: '' })
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-legal-primary px-6 py-4">
          <h2 className="text-xl font-semibold text-white">New Case Analysis</h2>
          <p className="text-blue-200 text-sm mt-1">
            Enter your case details to begin multi-agent legal analysis
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Case Title
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
              placeholder="e.g., Smith v. Johnson Corp."
            />
          </div>

          {/* Facts */}
          <div>
            <label htmlFor="facts" className="block text-sm font-medium text-gray-700 mb-2">
              Case Facts
            </label>
            <textarea
              id="facts"
              name="facts"
              value={formData.facts}
              onChange={handleChange}
              required
              rows={10}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow resize-y"
              placeholder="Describe the key facts of the case, including relevant dates, parties involved, and the dispute..."
            />
          </div>

          {/* Jurisdiction and Stakes row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="jurisdiction" className="block text-sm font-medium text-gray-700 mb-2">
                Jurisdiction
              </label>
              <input
                type="text"
                id="jurisdiction"
                name="jurisdiction"
                value={formData.jurisdiction}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                placeholder="e.g., California State Law"
              />
            </div>

            <div>
              <label htmlFor="stakes" className="block text-sm font-medium text-gray-700 mb-2">
                Stakes / Damages Sought
              </label>
              <input
                type="text"
                id="stakes"
                name="stakes"
                value={formData.stakes}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                placeholder="e.g., $500,000 in damages"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap items-center justify-between pt-4 border-t border-gray-200">
            <div className="flex gap-3 mb-4 md:mb-0">
              <button
                type="button"
                onClick={handleLoadDemo}
                className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Load Demo Case
              </button>
              <button
                type="button"
                onClick={handleClear}
                className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Clear Form
              </button>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="px-8 py-3 bg-legal-primary hover:bg-legal-secondary text-white font-semibold rounded-lg shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Submitting...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Begin Analysis
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Info Card - Suits themed */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="font-semibold text-blue-800 mb-3">Meet Your Legal Council (Inspired by Suits)</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm text-blue-700">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center flex-shrink-0 font-bold">H</div>
            <p><strong>Harvey</strong> - Lead Strategist who develops bold, winning strategies</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center flex-shrink-0 font-bold">L</div>
            <p><strong>Louis</strong> - Precedent Expert who masters case law research</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center flex-shrink-0 font-bold">T</div>
            <p><strong>Tanner</strong> - Adversarial Counsel who attacks your strategy</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center flex-shrink-0 font-bold">J</div>
            <p><strong>Jessica</strong> - Managing Partner who synthesizes final strategy</p>
          </div>
        </div>
        <p className="mt-4 text-xs text-blue-600">
          Harvey and Tanner will debate your strategy in multiple rounds before Jessica delivers the final verdict.
        </p>
      </div>
    </div>
  )
}

export default CaseInput
