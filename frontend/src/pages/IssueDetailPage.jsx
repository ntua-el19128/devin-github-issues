import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useRepo } from '../context/RepoContext'
import { api } from '../api'
import Button from '../components/Button'
import EmptyState from '../components/EmptyState'
import ExecutionResults from '../components/ExecutionResults'

export default function IssueDetailPage() {
  const { number } = useParams()
  const issueNumber = parseInt(number, 10)  
  const { repo } = useRepo()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [issue, setIssue] = useState(null)

  const [running, setRunning] = useState(false)
  const [resultSummary, setResultSummary] = useState('')
  const [resultData, setResultData] = useState(null)

  
  useEffect(() => {

  if (!localStorage.getItem("appSessionStarted")) {
    localStorage.setItem("appSessionStarted", "true")
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith("lastResults:") || key.startsWith("lastSummary:")) {
        localStorage.removeItem(key)
      }
    })
  }
}, [])

  // save results whenever they change
  useEffect(() => {
    if (resultData) {
      localStorage.setItem(`lastResults:${repo}`, JSON.stringify(resultData))
      localStorage.setItem(`lastSummary:${repo}`, resultSummary)
    }
  }, [repo, resultData, resultSummary])


  // fetch issue details
  useEffect(() => {
    let mounted = true
    setLoading(true); setError('')
    api.issue(repo, issueNumber)
      .then((data) => mounted && setIssue(data))
      .catch((e) => mounted && setError(e.message || 'Failed to load'))
      .finally(() => mounted && setLoading(false))
    return () => { mounted = false }
  }, [repo, issueNumber])

  async function runOne(n) {
    setRunning(true)
    setResultSummary('')
    setResultData(null)
    try {
      const res = await api.scopeAndExecuteBatch(repo, { all: false, issues: [n] })
      const item = res.results[0] || {}
      if (item.status === 'success') {
        setResultSummary(`Completed #${n}.`)
      } else {
        setResultSummary(`Failed #${n}: ${item.error || 'Unknown error'}`)
      }
      setResultData(res)
    } catch (e) {
      setResultSummary(`Failed #${n}: ${e.message}`)
      setResultData({ results: [{ issue_number: n, status: 'failed', error: e.message }] })
    } finally {
      setRunning(false)
    }
  }

  if (loading) return <EmptyState title="Loading…" />
  if (error) return <EmptyState title="Couldn’t load issue" description={error} />
  if (!issue) return null

  return (
    <div className="card">
      <div className="row">
        <h2 style={{ marginTop: 0, marginBottom: 8 }}>
          #{issue.number} : {issue.title}
        </h2>
        <span className="space" />
        <span className="badge">{issue.state}</span>
      </div>
      <div className="small" style={{ marginBottom: 10 }}>
        <a href={issue.url} target="_blank" rel="noreferrer">Open on GitHub ↗</a>
      </div>
      <div className="hr" />
      <pre style={{
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        background: '#0b0d12',
        border: '1px solid var(--border)',
        padding: 16,
        borderRadius: 10,
        maxHeight: 480,
        overflow: 'auto'
      }}>
        {issue.body || '(no description)'}
      </pre>

      <div className="row" style={{ marginTop: 16 }}>
        <Button variant="success" onClick={() => runOne(issue.number)} disabled={running}>
          {running ? 'Running…' : 'Scope & Execute'}
        </Button>
      </div>

      {resultSummary && <p className="small" style={{ marginTop: 10 }}>{resultSummary}</p>}
      <ExecutionResults resultData={resultData} />
    </div>
  )
}
