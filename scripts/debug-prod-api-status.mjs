#!/usr/bin/env node
/**
 * 生产 API 探测：将结果 POST 到 Cursor 调试 ingest（需本机 14040 服务可用）。
 * 用法：node scripts/debug-prod-api-status.mjs [baseUrl]
 * 默认 baseUrl: https://automata.biotools.bio
 */
const INGEST =
  'http://localhost:14040/ingest/6dc962d8-64eb-484b-bfba-ea5fdfdb97f2'
const SESSION = '474929'

const base = (process.argv[2] || 'https://automata.biotools.bio').replace(/\/$/, '')
const loginUrl = `${base}/api/v1/auth/login`

const r = await fetch(loginUrl, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
  body: JSON.stringify({ username: '_probe_', password: '_probe_' }),
})

const text = await r.text()
const server = r.headers.get('server')
const contentType = r.headers.get('content-type')
const apache503 =
  r.status === 503 &&
  typeof text === 'string' &&
  (text.includes('Apache Server') || text.includes('503 Service Unavailable'))

const data = {
  httpStatus: r.status,
  server,
  contentType,
  bodyPrefix: text.slice(0, 500),
  apache503,
  loginUrl,
  hypothesisA_apacheUpstreamDown: apache503,
  hypothesisB_json502App:
    r.status === 502 || (r.status === 503 && contentType?.includes('application/json')),
  hypothesisC_wrongPathOrCdn: r.status === 404,
}

const payload = {
  sessionId: SESSION,
  runId: process.env.DEBUG_RUN_ID || 'probe',
  hypothesisId: 'A',
  location: 'scripts/debug-prod-api-status.mjs',
  message: 'production API POST /api/v1/auth/login probe',
  data,
  timestamp: Date.now(),
}

await fetch(INGEST, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Debug-Session-Id': SESSION,
  },
  body: JSON.stringify(payload),
}).catch(() => {})

console.log(JSON.stringify(data, null, 2))
