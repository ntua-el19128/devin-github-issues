import { createContext, useContext, useEffect, useState } from 'react'

const RepoContext = createContext(null)

export function RepoProvider({ children }) {
  const [repo, setRepo] = useState(() => localStorage.getItem('repo') || '')

  useEffect(() => {
    if (repo) localStorage.setItem('repo', repo)
    else localStorage.removeItem('repo')
  }, [repo])

  return (
    <RepoContext.Provider value={{ repo, setRepo }}>
      {children}
    </RepoContext.Provider>
  )
}

export function useRepo() {
  const ctx = useContext(RepoContext)
  if (!ctx) throw new Error('useRepo must be used within RepoProvider')
  return ctx
}
