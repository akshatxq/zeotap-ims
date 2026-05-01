import React, { useState } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

function RCAForm({ workItemId, onComplete }) {
  const [formData, setFormData] = useState({
    incident_start: '',
    incident_end: '',
    root_cause_category: 'INFRA',
    fix_applied: '',
    prevention_steps: '',
    impact_description: ''
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const categories = ['INFRA', 'CODE', 'CONFIG', 'NETWORK']

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
    setError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/work-items/${workItemId}/rca`, formData)
      setSuccess(true)
      setTimeout(() => {
        onComplete()
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit RCA')
      setSubmitting(false)
    }
  }

  if (success) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 mt-6">
        <div className="text-center">
          <div className="text-green-800 font-semibold text-lg mb-2">
            ✅ RCA Submitted Successfully!
          </div>
          <div className="text-green-600">
            Incident has been closed. Redirecting...
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mt-6">
      <h3 className="text-xl font-bold mb-4">Root Cause Analysis (RCA)</h3>
      <p className="text-gray-600 mb-4 text-sm">
        Complete this form to close the incident. All fields are required.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Incident Start Time *
            </label>
            <input
              type="datetime-local"
              name="incident_start"
              required
              value={formData.incident_start}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Incident End Time *
            </label>
            <input
              type="datetime-local"
              name="incident_end"
              required
              value={formData.incident_end}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Root Cause Category *
          </label>
          <select
            name="root_cause_category"
            required
            value={formData.root_cause_category}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Fix Applied * (minimum 20 characters)
          </label>
          <textarea
            name="fix_applied"
            required
            rows="3"
            value={formData.fix_applied}
            onChange={handleChange}
            placeholder="Describe the fix that was applied to resolve the incident..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            {formData.fix_applied.length}/20 characters minimum
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Prevention Steps * (minimum 20 characters)
          </label>
          <textarea
            name="prevention_steps"
            required
            rows="3"
            value={formData.prevention_steps}
            onChange={handleChange}
            placeholder="Describe steps to prevent this from happening again..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            {formData.prevention_steps.length}/20 characters minimum
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Impact Description (Optional)
          </label>
          <textarea
            name="impact_description"
            rows="2"
            value={formData.impact_description}
            onChange={handleChange}
            placeholder="Describe the business impact of this incident..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={onComplete}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? 'Submitting...' : 'Submit RCA & Close Incident'}
          </button>
        </div>
      </form>

      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
        <p className="text-sm text-yellow-800">
          ⚠️ <strong>Note:</strong> RCA validation rules:
          <br />
          - Fix and prevention steps must be at least 20 characters
          <br />
          - End time must be after start time
          <br />
          - All fields except impact description are required
        </p>
      </div>
    </div>
  )
}

export default RCAForm