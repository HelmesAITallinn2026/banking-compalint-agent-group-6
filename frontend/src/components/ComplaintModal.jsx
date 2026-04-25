import { useEffect, useState } from 'react'
import { getComplaintAttachments, getAttachmentFileUrl } from '../api'
import AgentTimeline from './AgentTimeline'

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatBytes(bytes) {
  if (bytes == null) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function ComplaintModal({
  complaint, onClose, onApprove, approving, isDraft,
  onGenerateDraft, generating, isRecommendationReady,
}) {
  const [attachments, setAttachments] = useState([])

  // Close on Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  useEffect(() => {
    getComplaintAttachments(complaint.id)
      .then(setAttachments)
      .catch(() => setAttachments([]))
  }, [complaint.id])

  const name =
    complaint.customerName ||
    [complaint.customerFirstName, complaint.customerLastName].filter(Boolean).join(' ') ||
    `Customer #${complaint.customerId}`

  const recommendedDecision =
    complaint.recommendation === 'NEGATIVE' ? 'NEGATIVE' : 'POSITIVE'
  const alternateDecision = recommendedDecision === 'POSITIVE' ? 'NEGATIVE' : 'POSITIVE'

  return (
    <div
      className="modal-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <button className="modal__close" onClick={onClose} aria-label="Close">✕</button>

        <h2 className="modal__title" id="modal-title">{complaint.subject}</h2>

        <div className="modal__section">
          <div className="modal__label">Customer</div>
          <div className="modal__value">{name}</div>
        </div>

        <div className="modal__section">
          <div className="modal__label">Status</div>
          <div className="modal__value">{complaint.status}</div>
        </div>

        <div className="modal__section">
          <div className="modal__label">Created</div>
          <div className="modal__value">{formatDate(complaint.createdDttm)}</div>
        </div>

        {complaint.refusalReason && (
          <div className="modal__section">
            <div className="modal__label">Refusal Reason</div>
            <div className="modal__value">{complaint.refusalReason}</div>
          </div>
        )}

        <hr className="modal__divider" />

        <div className="modal__section">
          <div className="modal__label">Description</div>
          <div className="modal__value">{complaint.text}</div>
        </div>

        {/* Agent processing data */}
        {complaint.category && (
          <div className="modal__section">
            <div className="modal__label">Category</div>
            <div className="modal__value">{complaint.category}</div>
          </div>
        )}

        {complaint.recommendation && (
          <div className="modal__section">
            <div className="modal__label">AI Recommendation</div>
            <div className="modal__value" style={{
              fontWeight: 600,
              color: complaint.recommendation === 'POSITIVE' ? '#0bdf50' : '#c41c1c',
            }}>
              {complaint.recommendation}
            </div>
          </div>
        )}

        {complaint.recommendationReasoning && (
          <div className="modal__section">
            <div className="modal__label">Recommendation Reasoning</div>
            <div className="modal__value" style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>
              {complaint.recommendationReasoning}
            </div>
          </div>
        )}

        {attachments.length > 0 && (
          <>
            <hr className="modal__divider" />
            <div className="modal__section">
              <div className="modal__label">Attachments ({attachments.length})</div>
              <ul style={{ listStyle: 'none', margin: '8px 0 0', padding: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {attachments.map((a) => (
                  <li key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <a
                      href={getAttachmentFileUrl(a.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ fontSize: 14, color: 'var(--color-text)', textDecoration: 'underline', wordBreak: 'break-all' }}
                    >
                      {a.fileName}
                    </a>
                    {a.fileSize != null && (
                      <span style={{ fontSize: 12, color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
                        {formatBytes(a.fileSize)}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}

        {/* Agent activity timeline */}
        <AgentTimeline complaintId={complaint.id} complaintStatus={complaint.status} />

        {/* Generate Draft buttons — shown when recommendation is ready */}
        {isRecommendationReady && onGenerateDraft && (
          <>
            <hr className="modal__divider" />
            <div className="modal__section">
              <div className="modal__label">Generate Draft Response</div>
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <button
                  className="btn btn--accent"
                  style={{ flex: 1 }}
                  onClick={() => onGenerateDraft(complaint.id, recommendedDecision)}
                  disabled={generating}
                >
                  {generating ? 'Generating…' : 'Maintain recommendation'}
                </button>
                <button
                  className="btn btn--outline"
                  style={{ flex: 1 }}
                  onClick={() => onGenerateDraft(complaint.id, alternateDecision)}
                  disabled={generating}
                >
                  {generating ? 'Generating…' : `Reject recommendation (So decision will be ${alternateDecision})`}
                </button>
              </div>
            </div>
          </>
        )}

        {isDraft && (
          <>
            <hr className="modal__divider" />
            <div className="modal__draft-box">
              <div className="modal__section">
                <div className="modal__label">Draft Email Subject</div>
                <div className="modal__value">{complaint.draftEmailSubject || '—'}</div>
              </div>
              <div className="modal__section" style={{ marginBottom: 0 }}>
                <div className="modal__label">Draft Email Body</div>
                <div className="modal__value">{complaint.draftEmailBody || '—'}</div>
              </div>
            </div>
            <button
              className="btn btn--accent"
              style={{ width: '100%', marginTop: 8 }}
              onClick={() => onApprove(complaint.id)}
              disabled={approving}
            >
              {approving ? 'Approving…' : 'Approve & Send'}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
