import React, { useState, useEffect } from 'react'
import axios from 'axios'
import LiveFeed from './components/LiveFeed'
import IncidentList from './components/IncidentList'
import IncidentDetail from './components/IncidentDetail'
import RCAForm from './components/RCAForm'

const API_BASE = 'http://localhost:8000'

function App() {
  const [activeTab, setActiveTab] = useState('live')
  const [incidents, setIncidents] = useState([])
  const [selectedIncident, setSelectedIncident] = useState(null)
  const [metrics, setMetrics] = useState(null)

  useEffect(() => {
    fetchIncidents()
    fetchMetrics()
    const interval = setInterval(() => {
      fetchMetrics()
      fetchIncidents() // Refresh incidents periodically
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchIncidents = async () => {
    try {
      const response = await axios.get(`${API_BASE}/work-items`)
      setIncidents(response.data)
    } catch (error) {
      console.error('Error fetching incidents:', error)
    }
  }

  const fetchMetrics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/signals/metrics`)
      setMetrics(response.data)
    } catch (error) {
      console.error('Error fetching metrics:', error)
    }
  }

  const handleIncidentClick = (incident) => {
    setSelectedIncident(incident)
    setActiveTab('detail')
  }

  const handleBackToList = () => {
    setSelectedIncident(null)
    setActiveTab('incidents')
  }

  const handleRCAComplete = () => {
    fetchIncidents()
    setActiveTab('incidents')
    setSelectedIncident(null)
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold">Zeotap IMS</h1>
              <p className="text-blue-100 mt-1">Incident Management System</p>
            </div>
            {metrics && (
              <div className="bg-white/10 rounded-lg px-4 py-2">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-blue-200">Queue:</span>
                    <span className="ml-2 font-bold">{metrics.queue_depth}</span>
                  </div>
                  <div>
                    <span className="text-blue-200">Work Items:</span>
                    <span className="ml-2 font-bold">{metrics.work_items_created}</span>
                  </div>
                  <div>
                    <span className="text-blue-200">Debounced:</span>
                    <span className="ml-2 font-bold">{metrics.signals_debounced}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-md">
        <div className="container mx-auto px-4">
          <div className="flex space-x-4">
            <button
              onClick={() => {
                setActiveTab('live')
                setSelectedIncident(null)
              }}
              className={`px-4 py-3 font-medium transition-colors ${
                activeTab === 'live'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Live Feed
            </button>
            <button
              onClick={() => {
                setActiveTab('incidents')
                setSelectedIncident(null)
              }}
              className={`px-4 py-3 font-medium transition-colors ${
                activeTab === 'incidents'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Active Incidents
            </button>
            <button
              onClick={() => {
                setActiveTab('metrics')
                setSelectedIncident(null)
              }}
              className={`px-4 py-3 font-medium transition-colors ${
                activeTab === 'metrics'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              System Metrics
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'live' && <LiveFeed />}
        {activeTab === 'incidents' && (
          <IncidentList incidents={incidents} onIncidentClick={handleIncidentClick} />
        )}
        {activeTab === 'detail' && selectedIncident && (
          <div>
            <button
              onClick={handleBackToList}
              className="mb-4 text-blue-600 hover:text-blue-800 flex items-center gap-2"
            >
              ← Back to Incidents
            </button>
            <IncidentDetail incident={selectedIncident} />
            <RCAForm workItemId={selectedIncident.id} onComplete={handleRCAComplete} />
          </div>
        )}
        {activeTab === 'metrics' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold mb-4">System Metrics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-lg mb-2">Queue Health</h3>
                <pre className="bg-gray-50 p-4 rounded overflow-auto">
                  {JSON.stringify(metrics, null, 2)}
                </pre>
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-2">API Endpoints</h3>
                <ul className="space-y-2">
                  <li><code className="bg-gray-100 px-2 py-1 rounded">POST /signals</code> - Ingest signals</li>
                  <li><code className="bg-gray-100 px-2 py-1 rounded">GET /signals/metrics</code> - View metrics</li>
                  <li><code className="bg-gray-100 px-2 py-1 rounded">GET /health</code> - Health check</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App