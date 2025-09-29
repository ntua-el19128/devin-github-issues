import { Routes, Route, Navigate } from 'react-router-dom'
import RepoPage from './pages/RepoPage'
import IssuesPage from './pages/IssuesPage'
import IssueDetailPage from './pages/IssueDetailPage'
import Header from './components/Header'
import { useRepo } from './context/RepoContext'

export default function App() {
  const { repo } = useRepo()

  return (
    <>
      <Header />
      <div className="container">
        <Routes>
          <Route path="/" element={<RepoPage />} />
          <Route
            path="/issues"
            element={repo ? <IssuesPage /> : <Navigate to="/" replace />}
          />
          <Route
            path="/issues/:number"
            element={repo ? <IssueDetailPage /> : <Navigate to="/" replace />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </>
  )
}
