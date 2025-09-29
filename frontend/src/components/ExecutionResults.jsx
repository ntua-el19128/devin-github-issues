export default function ExecutionResults({ resultData }) {
  if (!resultData || !resultData.results) return null

  return (
    <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
      {resultData.results.map(r => (
        <div
          key={r.issue_number}
          style={{
            background: '#11161c',
            padding: 16,
            borderRadius: 10,
            border: '1px solid var(--border)',
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ fontSize: 15 }}>Issue #{r.issue_number}</strong>
            <span
              style={{
                padding: '2px 8px',
                borderRadius: 6,
                fontSize: 12,
                fontWeight: 600,
                color: r.status === 'success' ? 'var(--success-text)' : r.status === 'failed' ? 'var(--danger-text)' : 'var(--text-muted)',
                background: r.status === 'success'
                  ? 'rgba(0, 200, 0, 0.15)'
                  : r.status === 'failed'
                  ? 'rgba(200, 0, 0, 0.15)'
                  : 'rgba(255, 255, 255, 0.1)',
              }}
            >
              {r.status.toUpperCase()}
            </span>
          </div>

          {/* Success details */}
          {r.status === 'success' && (
            <div style={{ marginTop: 10 }}>
              {r.scoped?.summary && (
                <p style={{ margin: '4px 0', fontSize: 14 }}>
                  <strong>Summary:</strong> {r.scoped.summary}
                </p>
              )}
              {r.scoped?.confidence_score && (
                <p style={{ margin: '4px 0', fontSize: 14 }}>
                  <strong>Confidence:</strong> {r.scoped.confidence_score}
                </p>
              )}
              {r.executed?.branch_name && (
                <p style={{ margin: '4px 0', fontSize: 14 }}>
                  <strong>Branch:</strong> <code>{r.executed.branch_name}</code>
                </p>
              )}
              {r.executed?.pull_request_url && (
                <p style={{ margin: '4px 0', fontSize: 14 }}>
                  <strong>PR:</strong>{' '}
                  <a href={r.executed.pull_request_url} target="_blank" rel="noreferrer">
                    View Pull Request ↗
                  </a>
                </p>
              )}
              {r.executed?.commits?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <strong>Commits:</strong>
                  <ul style={{ margin: '4px 0 0 16px' }}>
                    {r.executed.commits.map((c, i) => (
                      <li key={i} style={{ fontSize: 13 }}>
                        {typeof c === 'string' ? c : c.message || JSON.stringify(c)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Failure details */}
          {r.status === 'failed' && (
            <p style={{ marginTop: 10, fontSize: 14, color: 'var(--danger-text)' }}>
              <strong>Error:</strong> {r.error || 'Unknown failure'}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
