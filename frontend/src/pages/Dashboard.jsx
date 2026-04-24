import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { getComplaints, approveComplaint, generateDraft } from '../api'
import ComplaintCard from '../components/ComplaintCard'
import ComplaintModal from '../components/ComplaintModal'
import Spinner from '../components/Spinner'

const TABS = [
  {
    label: 'Submitted / In Process',
    statuses: ['Submitted', 'Data Extracted', 'Categorised', 'Decision Recommendation Created'],
  },
  { label: 'Draft Created', statuses: ['Draft Created'] },
  { label: 'Completed',     statuses: ['Completed'] },
]

export default function Dashboard() {
  const [activeTab,          setActiveTab]          = useState(0)
  const [complaints,         setComplaints]         = useState([])
  const [loading,            setLoading]            = useState(true)
  const [error,              setError]              = useState(null)
  const [selectedComplaint,  setSelectedComplaint]  = useState(null)
  const [approving,          setApproving]          = useState(false)
  const [generating,         setGenerating]         = useState(false)
  const [feedback,           setFeedback]           = useState(null)

  const loadComplaints = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getComplaints()
      setComplaints(Array.isArray(data) ? data : [])
    } catch {
      setError('Failed to load complaints. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadComplaints() }, [loadComplaints])

  const visibleComplaints = complaints.filter((c) =>
    TABS[activeTab].statuses.includes(c.status)
  )

  const handleApprove = async (complaintId) => {
    setApproving(true)
    try {
      await approveComplaint(complaintId)
      setFeedback({ type: 'success', message: 'Complaint approved and email sent.' })
      setSelectedComplaint(null)
      await loadComplaints()
    } catch {
      setFeedback({ type: 'error', message: 'Approval failed. Please try again.' })
    } finally {
      setApproving(false)
    }
  }

  const handleGenerateDraft = async (complaintId, decision) => {
    setGenerating(true)
    try {
      await generateDraft(complaintId, decision)
      setFeedback({ type: 'success', message: 'Draft generation triggered. Refresh in a moment to see results.' })
      setSelectedComplaint(null)
      setTimeout(loadComplaints, 3000)
    } catch {
      setFeedback({ type: 'error', message: 'Failed to trigger draft generation.' })
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="page-container">
      <Link to="/" className="back-link">← Home</Link>

      <header className="page-header">
        <h1>Operator Dashboard</h1>
      </header>

      {feedback && (
        <div className={`feedback feedback--${feedback.type}`}>
          <span>{feedback.message}</span>
          <button
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}
            onClick={() => setFeedback(null)}
          >
            ✕
          </button>
        </div>
      )}

      <div className="tabs">
        {TABS.map((tab, i) => (
          <button
            key={i}
            className={`tab ${activeTab === i ? 'tab--active' : ''}`}
            onClick={() => setActiveTab(i)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <Spinner />
      ) : error ? (
        <div className="error-state">
          {error}
          <br />
          <button className="btn btn--outline btn--sm" style={{ marginTop: 16 }} onClick={loadComplaints}>
            Retry
          </button>
        </div>
      ) : visibleComplaints.length === 0 ? (
        <div className="empty-state">No complaints in this category.</div>
      ) : (
        <div className="card-grid">
          {visibleComplaints.map((c) => (
            <ComplaintCard key={c.id} complaint={c} onClick={() => setSelectedComplaint(c)} />
          ))}
        </div>
      )}

      {selectedComplaint && (
        <ComplaintModal
          complaint={selectedComplaint}
          onClose={() => setSelectedComplaint(null)}
          onApprove={handleApprove}
          approving={approving}
          onGenerateDraft={handleGenerateDraft}
          generating={generating}
          isDraft={TABS[1].statuses.includes(selectedComplaint.status)}
          isRecommendationReady={selectedComplaint.status === 'Decision Recommendation Created'}
        />
      )}
    </div>
  )
}
