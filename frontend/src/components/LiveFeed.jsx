import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

function LiveFeed() {
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchRecentSignals()
    const interval = setInterval(fetchRecentSignals, 3000)
    return () => clearInterval(interval)
  }, [])

  const fetchRecentSignals = async () => {
    try {
      const response = await axios.get(`${API_BASE}/signals/recent`)
      setSignals(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching signals:', error)
      setLoading(false)
    }
  }

  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'P0': return 'bg-red-600'
      case 'P1': return 'bg-orange-500'
      case 'P2': return 'bg-yellow-500'
      default: return 'bg-gray-500'
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading live feed...</div>
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Live Signal Feed</h2>
      <div className="space-y-2">
        {signals.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No signals received yet</p>
        ) : (
          signals.map((signal, index) => (
            <div key={index} className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${getSeverityColor(signal.severity)} animate-pulse`}></div>
                  <span className="font-mono text-sm text-gray-500">
                    {new Date(signal.timestamp * 1000).toLocaleTimeString()}
                  </span>
                  <span className="font-semibold text-gray-700">{signal.component_id}</span>
                  <span className={`px-2 py-1 rounded text-xs font-bold text-white ${getSeverityColor(signal.severity)}`}>
                    {signal.severity}
                  </span>
                </div>
                <div className="text-sm text-gray-500">
                  {signal.error_type}
                </div>
              </div>
              {signal.message && (
                <div className="mt-2 text-sm text-gray-600">
                  {signal.message}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default LiveFeed