import { useNavigate } from 'react-router-dom'

// Mock customer ID matching the seeded customer in the database
const MOCK_CUSTOMER_ID = 1

export default function Home() {
  const navigate = useNavigate()

  return (
    <div className="home-page">
      <h1>Banking<br />Complaint Agent</h1>
      <p>Submit a complaint or manage open cases.</p>
      <div className="home-actions">
        <button className="btn btn--primary" onClick={() => navigate('/dashboard')}>
          Dashboard
        </button>
        <button className="btn btn--outline" onClick={() => navigate(`/customer/${MOCK_CUSTOMER_ID}`)}>
          Customer View
        </button>
      </div>
    </div>
  )
}
