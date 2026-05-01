import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

function IncidentDetail({ incident }) {
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(true)
  const [transitionEvent, setTransitionEvent] = useState('')
  const [transitioning, setTransitioning] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDetails()
  }, [incident.id])

  const fetchDetails = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE}/work-items/${incident.id}`)
      setDetails(response.data)
      setError(null)
    } catch (error) {
      console.error('Error fetching details:', error)
      setError('Failed to load incident details. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleTransition = async () => {
    if (!transitionEvent) return
    
    setTransitioning(true)
    try {
      await axios.post(`${API_BASE}/work-items/${incident.id}/transition?event=${transitionEvent}`)
      await fetchDetails() // Refresh details after transition
      setTransitionEvent('')
    } catch (error) {
      console.error('Error transitioning:', error)
      alert(error.response?.data?.detail || 'Transition failed')
    } finally {
      setTransitioning(false)
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      OPEN: 'bg-red-100 text-red-800',
      INVESTIGATING: 'bg-yellow-100 text-yellow-800',
      RESOLVED: 'bg-green-100 text-green-800',
      CLOSED: 'bg-gray-100 text-gray-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getSeverityColor = (severity) => {
    const colors = {
      P0: 'bg-red-600 text-white',
      P1: 'bg-orange-500 text-white',
      P2: 'bg-yellow-500 text-white'
    }
    return colors[severity] || 'bg-gray-500 text-white'
  }

  const getAvailableTransitions = (status) => {
    const transitions = {
      'OPEN': ['start_investigation'],
      'INVESTIGATING': ['resolve', 'escalate'],
      'RESOLVED': ['close', 'reopen'],
      'CLOSED': ['reopen']
    }
    return transitions[status] || []
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">
          <div className="text-gray-500">Loading incident details...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">
          <div className="text-red-500">{error}</div>
          <button 
            onClick={fetchDetails}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!details) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">
          <div className="text-gray-500">No incident details available</div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="border-b pb-4 mb-4">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold mb-2">Incident Details</h2>
            <p className="font-mono text-sm text-gray-500">{details.id}</p>
          </div>
          <div className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(details.status)}`}>
            {details.status}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="text-sm text-gray-500">Component</label>
          <p className="font-semibold">{details.component_id}</p>
        </div>
        <div>
          <label className="text-sm text-gray-500">Severity</label>
          <div>
            <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${getSeverityColor(details.severity)}`}>
              {details.severity}
            </span>
          </div>
        </div>
        <div>
          <label className="text-sm text-gray-500">Created At</label>
          <p className="font-semibold">{new Date(details.created_at).toLocaleString()}</p>
        </div>
        {details.mttr_minutes && (
          <div>
            <label className="text-sm text-gray-500">MTTR</label>
            <p className="font-semibold">{details.mttr_minutes} minutes</p>
          </div>
        )}
      </div>

      {/* State Transition Section */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-semibold text-lg mb-3">State Transition</h3>
        <div className="flex gap-3">
          <select
            value={transitionEvent}
            onChange={(e) => setTransitionEvent(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select transition...</option>
            {getAvailableTransitions(details.status).map(event => (
              <option key={event} value={event}>
                {event.replace('_', ' ').toUpperCase()}
              </option>
            ))}
          </select>
          <button
            onClick={handleTransition}
            disabled={!transitionEvent || transitioning}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {transitioning ? 'Processing...' : 'Execute Transition'}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Current Status: <strong>{details.status}</strong>
        </p>
      </div>

      {/* Signals Section */}
      {details.signals && details.signals.length > 0 && (
        <div>
          <h3 className="font-semibold text-lg mb-3">Linked Signals ({details.signals.length})</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {details.signals.map((signal, idx) => (
              <div key={idx} className="bg-gray-50 rounded p-3">
                <div className="flex justify-between text-sm">
                  <span className="font-mono">{signal.error_type}</span>
                  <span className="text-gray-500">
                    {signal.timestamp ? new Date(signal.timestamp * 1000).toLocaleString() : 'Unknown time'}
                  </span>
                </div>
                {signal.message && (
                  <div className="text-sm text-gray-600 mt-1">{signal.message}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default IncidentDetail