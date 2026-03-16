/**
 * 请求追踪工具
 * 统一生成 request id，并从响应头里拿回后端最终使用的 request id。
 */

const REQUEST_ID_HEADER = 'X-Request-Id'

export function newRequestId(prefix = 'web'): string {
  const ts = Date.now().toString(36)
  const rand = Math.random().toString(36).slice(2, 10)
  return `${prefix}-${ts}-${rand}`
}

export function getResponseRequestId(resp: Response, fallback = ''): string {
  return (
    resp.headers.get(REQUEST_ID_HEADER) ||
    resp.headers.get('X-Request-ID') ||
    fallback
  ).trim()
}

export function buildRequestTraceHeaders(requestId: string): Record<string, string> {
  return { [REQUEST_ID_HEADER]: requestId }
}
