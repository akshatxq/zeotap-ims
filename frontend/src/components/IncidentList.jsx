import React from 'react'

function IncidentList({ incidents, onIncidentClick }) {
  const getSeverityBadge = (severity) => {
    const colors = {
      P0: 'bg-red-600 text-white',
      P1: 'bg-orange-500 text-white',
      P2: 'bg-yellow-500 text-white'
    }
    return `px-2 py-1 rounded text-xs font-bold ${colors[severity] || 'bg-gray-500 text-white'}`
  }

  const getStatusBadge = (status) => {
    const colors = {
      OPEN: 'bg-red-100 text-red-800',
      INVESTIGATING: 'bg-yellow-100 text-yellow-800',
      RESOLVED: 'bg-green-100 text-green-800',
      CLOSED: 'bg-gray-100 text-gray-800'
    }
    return `px-2 py-1 rounded text-xs font-bold ${colors[status] || 'bg-gray-100 text-gray-800'}`
  }

  if (!incidents || incidents.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No active incidents</p>
      </div>
    )
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Active Incidents</h2>
      <div className="grid gap-4">
        {incidents.map((incident) => (
          <div
            key={incident.id}
            onClick={() => onIncidentClick(incident)}
            className="bg-white rounded-lg shadow p-4 hover:shadow-lg cursor-pointer transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="font-mono text-sm text-gray-500">{incident.id.slice(-8)}</span>
                  <span className={getSeverityBadge(incident.severity)}>{incident.severity}</span>
                  <span className={getStatusBadge(incident.status)}>{incident.status}</span>
                </div>
                <div className="font-semibold text-gray-800">{incident.component_id}</div>
                <div className="text-sm text-gray-500 mt-1">
                  Created: {new Date(incident.created_at).toLocaleString()}
                </div>
              </div>
              <div className="text-right text-sm text-gray-500">
                Click to view details →
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default IncidentList