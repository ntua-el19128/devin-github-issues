const BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

async function _req(path, opts = {}) {
  const url = `${BASE}/${path.replace(/^\/+/, '')}`;
  const method = (opts.method || 'GET').toUpperCase();
  const headers =
    method === 'GET' ? (opts.headers || {}) : { 'Content-Type': 'application/json', ...(opts.headers || {}) };

  const res = await fetch(url, { ...opts, method, headers });
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = { detail: text }; }
  if (!res.ok) throw new Error((data && (data.detail || data.message)) || `HTTP ${res.status}`);
  return data;
}
export const api = {
  issues(repo) { return _req(`${repo}/issues`); },
  issue(repo, number) { return _req(`${repo}/issues/${number}`); },
  scope(repo, number) { return _req(`${repo}/issues/${number}/scope`, { method: 'POST' }); },
  scopeAndExecute(repo, number) { return _req(`${repo}/issues/${number}/scope-and-execute`, { method: 'POST' }); },
  scopeAndExecuteBatch(repo, { all = false, issues = [], stop_on_error = false } = {}) {
    return _req(`${repo}/issues/scope-and-execute-batch`, {
      method: 'POST',
      body: JSON.stringify({ all, issues, stop_on_error })
    });
  }
};