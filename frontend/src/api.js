export async function request(url, { method = 'GET', body, token } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(url, {
    method,
    headers,
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })
  let data
  try {
    data = await res.json()
  } catch {
    throw new Error('The server returned an invalid response.')
  }
  return { ok: res.ok, status: res.status, data }
}

export const get = (url, token) => request(url, { token })
export const post = (url, body, token) => request(url, { method: 'POST', body, token })
export const put = (url, body, token) => request(url, { method: 'PUT', body, token })
export const remove = (url, token) => request(url, { method: 'DELETE', token })

export const fmt = (iso) => new Date(iso).toLocaleString()