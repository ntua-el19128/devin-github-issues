import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useRepo } from '../context/RepoContext'
import Button from '../components/Button'
import EmptyState from '../components/EmptyState'
import { api } from '../api'

export default function RepoPage() {
  const { repo, setRepo } = useRepo()
  const [value, setValue] = useState(repo)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const nav = useNavigate()

  async function continueToIssues(e) {
    e.preventDefault()
    setError('')
    const trimmed = (value || '').trim()
    if (!trimmed) { setError('Enter a repository name (e.g. my-repo)'); return }
    setLoading(true)
    try {
      // ensuring repo exists and warming the server cache
      await api.issues(trimmed)
      setRepo(trimmed)
      nav('/issues')
    } catch (err) {
      setError(err.message || 'Failed to fetch issues')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="card" style={{ maxWidth: 680, margin: '40px auto' }}>
        <h2 style={{ marginTop: 0 }}>Select a repository</h2>
        <p className="small">
          i need just the repo name (the owner is configured on the backend via)
        </p>
        <form onSubmit={continueToIssues} className="row wrap" style={{ marginTop: 16 }}>
          <input
            className="input"
            placeholder="e.g. my-repo"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
          <Button variant="primary" disabled={loading}>
            {loading ? 'Loading…' : 'Continue'}
          </Button>
        </form>
        {error && <p className="small" style={{ color: 'var(--danger)', marginTop: 10 }}>{error}</p>}
        <div className="hr" />
        <EmptyState
          title="Tip"
          description={
            <>
              The app shows issues (not PRs).  
              Use <kbd>Scope &amp; Execute</kbd> to run Devin on one or many.
            </>
          }
        />
      </div>
    </div>
  )
}
