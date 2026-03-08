import { toNumber } from '@/shared/format'

export type TrendPoint = {
  date: string
  value: number
}

export type TrendItem = {
  code: string
  resolved_code?: string
  kind?: string
  label?: string
  points: TrendPoint[]
}

export function buildTrendSparklinePath(points: TrendPoint[], width = 120, height = 40): string {
  const usable = (points || []).filter((item) => item && item.date && Number.isFinite(toNumber(item.value)))
  if (usable.length < 2) return ''

  const top = 5
  const bottom = Math.max(top + 1, height - 5)
  const values = usable.map((item) => toNumber(item.value, 0))
  const minVal = Math.min(...values)
  const maxVal = Math.max(...values)
  const range = Math.max(maxVal - minVal, 1)

  const chartPoints = usable.map((item, index) => {
    const x = (width / (usable.length - 1)) * index
    const ratio = (toNumber(item.value, 0) - minVal) / range
    const y = maxVal === minVal ? (top + bottom) / 2 : bottom - ratio * (bottom - top)
    return { x, y }
  })

  const first = chartPoints[0]
  const second = chartPoints[1]
  const last = chartPoints[chartPoints.length - 1]
  const lastControl = chartPoints[chartPoints.length - 2]
  if (!first || !second || !last || !lastControl) return ''

  let path = `M${first.x.toFixed(1)},${first.y.toFixed(1)}`
  if (chartPoints.length === 2) {
    path += ` L${second.x.toFixed(1)},${second.y.toFixed(1)}`
    return path
  }

  for (let i = 1; i < chartPoints.length - 1; i += 1) {
    const control = chartPoints[i]
    const next = chartPoints[i + 1]
    if (!control || !next) continue
    const midX = (control.x + next.x) / 2
    const midY = (control.y + next.y) / 2
    path += ` Q${control.x.toFixed(1)},${control.y.toFixed(1)} ${midX.toFixed(1)},${midY.toFixed(1)}`
  }

  path += ` Q${lastControl.x.toFixed(1)},${lastControl.y.toFixed(1)} ${last.x.toFixed(1)},${last.y.toFixed(1)}`
  return path
}
