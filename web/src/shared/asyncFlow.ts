export type AsyncFlowResult = {
  flow: string
  ok: boolean
  stage: string
  startedAt: string
  endedAt: string
  durationMs: number
  error?: string
}

type AsyncFlowTracker = {
  flow: string
  stage: string
  startedAt: number
}

function logResult(result: AsyncFlowResult) {
  if (!import.meta.env.DEV) return
  const logger = result.ok ? console.debug : console.warn
  logger('[async-flow]', result)
}

export function startAsyncFlow(flow: string, stage = 'start'): AsyncFlowTracker {
  return {
    flow,
    stage,
    startedAt: Date.now(),
  }
}

export function finishAsyncFlow(
  tracker: AsyncFlowTracker,
  stage = 'done',
  error?: unknown,
): AsyncFlowResult {
  const endedAt = Date.now()
  const result: AsyncFlowResult = {
    flow: tracker.flow,
    ok: !error,
    stage,
    startedAt: new Date(tracker.startedAt).toISOString(),
    endedAt: new Date(endedAt).toISOString(),
    durationMs: endedAt - tracker.startedAt,
  }
  if (error) {
    result.error = error instanceof Error ? error.message : String(error)
  }
  logResult(result)
  return result
}
