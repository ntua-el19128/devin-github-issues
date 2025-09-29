import { Link } from 'react-router-dom'
import Button from './Button'

export default function IssueRow({
  issue,
  checked,
  onToggle,
  onRunOne,
  running
}) {
  return (
    <tr>
      <td style={{ width: 36 }}>
        <input
          type="checkbox"
          className="checkbox"
          checked={checked}
          onChange={() => onToggle(issue.number)}
          aria-label={`Select issue #${issue.number}`}
        />
      </td>
      <td style={{ width: 90 }}>
        <span className="badge">{issue.state}</span>
      </td>
      <td>
        <div>
          <Link to={`/issues/${issue.number}`}>#{issue.number}</Link>
          &nbsp;:&nbsp;{issue.title}
        </div>
        <div className="small">
          <a href={issue.url} target="_blank" rel="noreferrer">Open on GitHub ↗</a>
        </div>
      </td>
      <td style={{ textAlign: 'right', width: 260 }}>
        <Button
          variant="success"
          onClick={() => onRunOne(issue.number)}
          disabled={running}
          title="Scope & Execute this issue"
        >
          {running ? 'Running…' : 'Scope & Execute'}
        </Button>
      </td>
    </tr>
  )
}
