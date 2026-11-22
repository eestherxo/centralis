export async function post(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({ error: 'Unexpected server response.' }))
  return { ok: res.ok, status: res.status, data }
}

export const fmt = (iso) => new Date(iso).toLocaleString()