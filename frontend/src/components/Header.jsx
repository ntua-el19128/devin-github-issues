import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useRepo } from '../context/RepoContext'

export default function Header() {
  const { repo, setRepo } = useRepo()
  const nav = useNavigate()
  const loc = useLocation()

  function clearRepo() {
    setRepo('')
    if (loc.pathname !== '/') nav('/')
  }

  return (
    <div style={{ borderBottom: '1px solid var(--border)', background: '#0c0f16' }}>
      <div className="container" style={{ padding: '16px 20px' }}>
        <div className="row">
          <Link to="/" style={{ fontWeight: 700 }}>Issues Runner</Link>
          <div className="space" />
          {repo && (
            <div className="row">
              <span className="badge">repo</span>
              <span style={{ opacity: 0.9 }}>{repo}</span>
              <button className="btn ghost" onClick={clearRepo} title="Change repository">
                Change
              </button>
              <Link to="/issues">
                <button className="btn">Issues</button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
