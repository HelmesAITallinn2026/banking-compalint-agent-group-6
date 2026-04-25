import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getCustomer, getCustomerAccounts, getRefusalReasons, createComplaint } from '../api'
import { toEUR, formatCurrency, formatEUR } from '../utils/currency'
import Spinner from '../components/Spinner'

export default function CustomerAccount() {
  const { id } = useParams()

  // Data loading state
  const [customer,        setCustomer]        = useState(null)
  const [accounts,        setAccounts]        = useState([])
  const [reasons,         setReasons]         = useState([])
  const [selectedReason,  setSelectedReason]  = useState(null)
  const [loadingCustomer, setLoadingCustomer] = useState(true)
  const [loadingAccounts, setLoadingAccounts] = useState(true)
  const [customerError,   setCustomerError]   = useState(null)
  const [accountsError,   setAccountsError]   = useState(null)

  // Form state
  const [subject,        setSubject]        = useState('')
  const [text,           setText]           = useState('')
  const [files,          setFiles]          = useState([])
  const [submitting,     setSubmitting]     = useState(false)
  const [submitFeedback, setSubmitFeedback] = useState(null)

  useEffect(() => {
    setLoadingCustomer(true)
    getCustomer(id)
      .then((data) => { setCustomer(data); setCustomerError(null) })
      .catch(() => setCustomerError('Failed to load customer details.'))
      .finally(() => setLoadingCustomer(false))
  }, [id])

  useEffect(() => {
    setLoadingAccounts(true)
    getCustomerAccounts(id)
      .then((data) => { setAccounts(Array.isArray(data) ? data : []); setAccountsError(null) })
      .catch(() => setAccountsError('Failed to load accounts.'))
      .finally(() => setLoadingAccounts(false))
  }, [id])

  useEffect(() => {
    getRefusalReasons()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setReasons(data)
          setSelectedReason(data[Math.floor(Math.random() * data.length)])
        }
      })
      .catch(() => {})
  }, [])

  const totalEUR = accounts.reduce((acc, a) => {
    const converted = toEUR(a.balance, a.currency)
    return converted != null ? acc + converted : acc
  }, 0)

  const fullName = customer
    ? [customer.firstName, customer.lastName].filter(Boolean).join(' ')
    : ''

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!subject.trim() || !text.trim()) return

    setSubmitting(true)
    setSubmitFeedback(null)

    const formData = new FormData()
    formData.append('customerId', id)
    formData.append('subject', subject)
    formData.append('text', text)
    if (selectedReason) formData.append('refusalReasonId', selectedReason.id)
    Array.from(files).forEach((file) => formData.append('files', file))

    try {
      await createComplaint(formData)
      setSubmitFeedback({ type: 'success', message: 'Complaint submitted successfully.' })
      setSubject('')
      setText('')
      setFiles([])
      // Randomise reason for next submission
      if (reasons.length > 0) {
        setSelectedReason(reasons[Math.floor(Math.random() * reasons.length)])
      }
    } catch {
      setSubmitFeedback({ type: 'error', message: 'Submission failed. Please try again.' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page-container">
      <Link to="/" className="back-link">← Home</Link>

      <header className="page-header">
        <h1>Customer Account</h1>
      </header>

      {/* ── Account Details ─────────────────────── */}
      <div className="section-card">
        <h2 className="section-title">Account Details</h2>
        {loadingCustomer ? (
          <Spinner />
        ) : customerError ? (
          <div className="error-state">{customerError}</div>
        ) : customer ? (
          <div className="customer-profile">
            <div className="customer-profile__photo">
              <img
                src={`https://randomuser.me/api/portraits/men/${(customer.id % 70) + 1}.jpg`}
                alt={`${customer.firstName} ${customer.lastName}`}
                className="customer-photo"
              />
            </div>
            <div className="customer-profile__info">
              <div className="customer-profile__name">
                {customer.firstName}{customer.middleName ? ` ${customer.middleName}` : ''} {customer.lastName}
              </div>
              <div className="customer-profile__id">Customer ID &nbsp;#{customer.id}</div>
              <div className="customer-profile__fields">
                <div className="profile-field">
                  <div className="profile-field__label">First Name</div>
                  <div className="profile-field__value">{customer.firstName}</div>
                </div>
                <div className="profile-field">
                  <div className="profile-field__label">Last Name</div>
                  <div className="profile-field__value">{customer.lastName}</div>
                </div>
                <div className="profile-field">
                  <div className="profile-field__label">Date of Birth</div>
                  <div className="profile-field__value">{customer.dob}</div>
                </div>
                <div className="profile-field">
                  <div className="profile-field__label">Email</div>
                  <div className="profile-field__value">{customer.email}</div>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* ── Financial Details ────────────────────── */}
      <div className="section-card">
        <h2 className="section-title">Financial Details</h2>
        {loadingAccounts ? (
          <Spinner />
        ) : accountsError ? (
          <div className="error-state">{accountsError}</div>
        ) : accounts.length === 0 ? (
          <div className="empty-state">No accounts found.</div>
        ) : (
          <>
            <table className="accounts-table">
              <thead>
                <tr>
                  <th>Account Number</th>
                  <th>Type</th>
                  <th>Currency</th>
                  <th>Balance</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((acc) => (
                  <tr key={acc.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: 13 }}>{acc.accountNumber}</td>
                    <td>{acc.accountType}</td>
                    <td>{acc.currency}</td>
                    <td>{formatCurrency(acc.balance, acc.currency)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="total-row">
              Total (EUR approx.): <strong>{formatEUR(totalEUR)}</strong>
            </div>
          </>
        )}
      </div>

      {/* ── Complaint Form ───────────────────────── */}
      <div className="section-card">
        <h2 className="section-title">Submit a Complaint</h2>

        {submitFeedback && (
          <div className={`feedback feedback--${submitFeedback.type}`} style={{ marginBottom: 20 }}>
            <span>{submitFeedback.message}</span>
            <button
              style={{ background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}
              onClick={() => setSubmitFeedback(null)}
            >
              ✕
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-block">
            <label className="form-label">Name and Surname</label>
            <input
              className="form-input"
              value={loadingCustomer ? 'Loading...' : fullName}
              disabled
              readOnly
            />
          </div>

          <div className="form-block">
            <label className="form-label" htmlFor="subject">Subject</label>
            <input
              id="subject"
              className="form-input"
              placeholder="Brief subject of your complaint"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
            />
          </div>

          <div className="form-block">
            <label className="form-label" htmlFor="complaint-text">Description</label>
            <textarea
              id="complaint-text"
              className="form-textarea"
              placeholder="Describe your complaint in detail..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              required
            />
          </div>

          <div className="form-block">
            <label className="form-label">Refusal Reason</label>
            <select
              className="form-select"
              value={selectedReason?.id ?? ''}
              disabled
            >
              {reasons.length === 0 ? (
                <option>Loading reasons…</option>
              ) : (
                reasons.map((r) => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))
              )}
            </select>
          </div>

          <div className="form-block">
            <label className="form-label" htmlFor="files">Attachments</label>
            <input
              id="files"
              type="file"
              multiple
              className="form-input"
              style={{ padding: '8px 12px' }}
              onChange={(e) => setFiles(e.target.files)}
            />
          </div>

          <button
            type="submit"
            className="btn btn--primary"
            disabled={submitting || loadingCustomer}
          >
            {submitting ? 'Submitting…' : 'Submit Complaint'}
          </button>
        </form>
      </div>
    </div>
  )
}
