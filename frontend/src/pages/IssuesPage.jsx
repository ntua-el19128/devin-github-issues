import React, { useEffect, useMemo, useState } from 'react'
import { useRepo } from '../context/RepoContext'
import { api } from '../api'
import IssueRow from '../components/IssueRow'
import Button from '../components/Button'
import EmptyState from '../components/EmptyState'
import ExecutionResults from '../components/ExecutionResults'

export default function IssuesPage() {
  const { repo } = useRepo()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [issues, setIssues] = useState([])
  const [selected, setSelected] = useState(() => new Set())
  const [runningIds, setRunningIds] = useState(new Set())
  const [batchRunning, setBatchRunning] = useState(false)

  const [resultSummary, setResultSummary] = useState('')
  const [resultData, setResultData] = useState(null)

  // load saved results on mount or repo change
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


  useEffect(() => {
    if (resultData) {
      localStorage.setItem(`lastResults:${repo}`, JSON.stringify(resultData))
      localStorage.setItem(`lastSummary:${repo}`, resultSummary)
    }
  }, [repo, resultData, resultSummary])


  // fetch issues
  useEffect(() => {
    let mounted = true
    setLoading(true)
    setError('')
    api.issues(repo)
      .then((data) => {
        const list = data.issues || []
        if (mounted) setIssues(list)
      })
      .catch((e) => mounted && setError(e.message || 'Failed to load'))
      .finally(() => mounted && setLoading(false))
    return () => { mounted = false }
  }, [repo])

  const allChecked = useMemo(() => {
    return issues.length > 0 && selected.size === issues.length
  }, [issues, selected])

  function toggleOne(n) {
    const next = new Set(selected)
    if (next.has(n)) next.delete(n); else next.add(n)
    setSelected(next)
  }

  function toggleAll() {
    if (allChecked) setSelected(new Set())
    else setSelected(new Set(issues.map(i => i.number)))
  }

  // now using batch endpoint even for one issue
  async function runOne(n) {
    setRunningIds(prev => new Set([...prev, n]))
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
      setRunningIds(prev => {
        const next = new Set(prev)
        next.delete(n)
        return next
      })
    }
  }

  async function runSelected() {
    if (selected.size === 0) return
    setBatchRunning(true)
    setResultSummary('')
    setResultData(null)
    try {
      const res = await api.scopeAndExecuteBatch(repo, {
        all: false,
        issues: Array.from(selected)
      })
      setResultSummary(`Batch done: ${res.succeeded} succeeded, ${res.failed} failed.`)
      setResultData(res)
    } catch (e) {
      setResultSummary(`Batch failed: ${e.message}`)
      setResultData({ results: [] })
    } finally {
      setBatchRunning(false)
    }
  }

  async function runAll() {
    setBatchRunning(true)
    setResultSummary('')
    setResultData(null)
    try {
      const res = await api.scopeAndExecuteBatch(repo, { all: true })
      setResultSummary(`All issues: ${res.succeeded} succeeded, ${res.failed} failed.`)
      setResultData(res)
    } catch (e) {
      setResultSummary(`All issues failed: ${e.message}`)
      setResultData({ results: [] })
    } finally {
      setBatchRunning(false)
    }
  }

  if (loading) {
    return <EmptyState title="Loading issues…" description="Talking to GitHub via your backend." />
  }
  if (error) {
    return <EmptyState title="Couldn’t load issues" description={error} />
  }
  if (!issues || issues.length === 0) {
    return <EmptyState title="No issues found" description="This repository has no issues (or only PRs)." />
  }

  return (
    <div className="card">
      <div className="row" style={{ marginBottom: 10 }}>
        <h2 style={{ margin: 0 }}>Issues</h2>
        <div className="space" />
        <Button variant="success" onClick={runAll} disabled={batchRunning}>
          {batchRunning ? 'Running…' : 'Scope & Execute ALL'}
        </Button>
      </div>

      <div className="row" style={{ marginBottom: 8 }}>
        <label className="row" style={{ gap: 8 }}>
          <input
            type="checkbox"
            className="checkbox"
            checked={allChecked}
            onChange={toggleAll}
            aria-label="Select all"
          />
          <span className="small">Select all</span>
        </label>
        <div className="space" />
        <Button onClick={runSelected} disabled={selected.size === 0 || batchRunning}>
          {batchRunning ? 'Running…' : `Scope & Execute Selected (${selected.size})`}
        </Button>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th style={{ width: 36 }} />
            <th style={{ width: 90 }}>State</th>
            <th>Title</th>
            <th style={{ width: 260, textAlign: 'right' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {issues.map(issue => (
            <IssueRow
              key={issue.number}
              issue={issue}
              checked={selected.has(issue.number)}
              onToggle={toggleOne}
              onRunOne={runOne}
              running={runningIds.has(issue.number)}
            />
          ))}
        </tbody>
      </table>

      {resultSummary && <p className="small" style={{ marginTop: 10 }}>{resultSummary}</p>}
      <ExecutionResults resultData={resultData} />
    </div>
  )
}
