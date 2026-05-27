// 走 vite proxy /api -> http://127.0.0.1:8000，所以 base 直接是空
const BASE = ''

export async function fetchDraws({ page = 1, pageSize = 20 } = {}) {
  const r = await fetch(`${BASE}/api/toto/draws?page=${page}&page_size=${pageSize}`)
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}

export async function fetchLatest() {
  const r = await fetch(`${BASE}/api/toto/draws/latest`)
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}
