import { useEffect } from 'react'

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function ComplaintModal({ complaint, onClose, onApprove, approving, isDraft }) {
  // Close on Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  const name =
    complaint.customerName ||
    [complaint.customerFirstName, complaint.customerLastName].filter(Boolean).join(' ') ||
    `Customer #${complaint.customerId}`

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
