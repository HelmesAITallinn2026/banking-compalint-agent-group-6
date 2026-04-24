function statusClass(status) {
  return status
    ?.toLowerCase()
    .replace(/[\s/]+/g, '-')
    .replace(/[^a-z0-9-]/g, '') ?? ''
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

export default function ComplaintCard({ complaint, onClick }) {
  const name =
    complaint.customerName ||
    [complaint.customerFirstName, complaint.customerLastName].filter(Boolean).join(' ') ||
    `Customer #${complaint.customerId}`

  return (
    <div
      className="card card--clickable"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
    >
      <div className="complaint-card__title">{complaint.subject}</div>
      <div className="complaint-card__meta">{name}</div>
      <div className="complaint-card__meta">Created: {formatDate(complaint.createdDttm)}</div>
      <div className={`complaint-card__status status--${statusClass(complaint.status)}`}>
        {complaint.status}
      </div>
    </div>
  )
}
