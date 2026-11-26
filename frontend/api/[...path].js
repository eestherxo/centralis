export default async function handler(req, res) {
  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl) {
    res.status(503).json({ error: 'The API is not configured. Set BACKEND_URL in Vercel.' })
    return
  }

  const pathParts = req.query.path
  const path = Array.isArray(pathParts) ? pathParts.join('/') : String(pathParts || '')
  if (!path || path.includes('..')) {
    res.status(400).json({ error: 'Invalid API path.' })
    return
  }

  const backend = new URL(backendUrl)
  if (!['http:', 'https:'].includes(backend.protocol)) {
    res.status(500).json({ error: 'BACKEND_URL must use HTTP or HTTPS.' })
    return
  }
  const encodedPath = path.split('/').map(encodeURIComponent).join('/')
  const basePath = backend.pathname.replace(/\/+$/, '')
  const target = new URL(`${basePath}/${encodedPath}`, backend.origin)
  const originalUrl = new URL(req.url, 'http://vercel.local')
  target.search = originalUrl.search

  try {
    const headers = {}
    for (const header of ['authorization', 'content-type', 'accept']) {
      if (req.headers[header]) headers[header] = req.headers[header]
    }
    const hasBody = !['GET', 'HEAD'].includes(req.method)
    const upstream = await fetch(target, {
      method: req.method,
      headers,
      ...(hasBody && req.body !== undefined
        ? { body: typeof req.body === 'string' ? req.body : JSON.stringify(req.body) }
        : {}),
    })

    res.status(upstream.status)
    for (const header of ['content-type', 'content-disposition', 'cache-control']) {
      const value = upstream.headers.get(header)
      if (value) res.setHeader(header, value)
    }
    res.send(Buffer.from(await upstream.arrayBuffer()))
  } catch {
    res.status(502).json({ error: 'Could not reach the configured API server.' })
  }
}
