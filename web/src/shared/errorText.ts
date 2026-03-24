import type { ApiError } from './http'

const CODE_TEXT_MAP: Record<string, string> = {
  AUTH_BOOTSTRAP_TIMEOUT: '登录状态检查超时，请稍后重试',
  INSUFFICIENT_CASH: '账户余额不足，请更换其他账户',
  CASH_ASSET_NOT_FOUND: '现金账户不存在',
  CASH_ASSET_UPDATE_FAILED: '现金账户更新失败，请稍后重试',
  INVALID_CASH_AMOUNT: '现金金额不合法',
  INVALID_VALUE: '数值不合法',
  INVALID_AMOUNT: '金额不合法',
  INVALID_ID: '记录标识不合法',
  MISSING_ID: '缺少记录标识',
  MISSING_CODE: '缺少资产代码',
  MISSING_REQUIRED_FIELDS: '缺少必填参数',
  ASSET_ADD_FAILED: '添加资产失败，请稍后重试',
  ASSET_BUY_FAILED: '买入失败，请稍后重试',
  ASSET_BUY_WITH_CASH_FAILED: '现金买入失败，请稍后重试',
  ASSET_SELL_FAILED: '卖出失败，请稍后重试',
  ASSET_SELL_TO_CASH_FAILED: '卖出回款失败，请稍后重试',
  ASSET_MODIFY_FAILED: '调整资产失败，请稍后重试',
  ASSET_DELETE_FAILED: '删除资产失败，请稍后重试',
  UNDO_FAILED: '撤销失败，请稍后重试',
  INVALID_CALENDAR_PERIOD: '时间范围不合法',
}

const MESSAGE_TEXT_MAP: Record<string, string> = {
  'Request failed: 400': '请求参数不合法，请检查后重试',
  'Request failed: 401': '登录状态已过期，请重新登录',
  'Request failed: 403': '没有权限执行这个操作',
  'Request failed: 404': '请求的内容不存在',
  'Request failed: 409': '请求冲突，请刷新后重试',
  'Request failed: 429': '请求太频繁，请稍后再试',
  'Request failed: 500': '服务器开小差了，请稍后重试',
  'Request failed: 502': '服务暂时不可用，请稍后重试',
  'Request failed: 503': '服务暂时不可用，请稍后重试',
  'Failed to fetch': '网络连接失败，请检查网络后重试',
  'NetworkError when attempting to fetch resource.': '网络连接失败，请检查网络后重试',
  'Missing required fields': '缺少必填参数',
  'Missing code': '缺少资产代码',
  'Missing dates': '缺少日期参数',
  'Missing id': '缺少记录标识',
  'Missing user_id': '缺少用户标识',
  'Missing scope_key': '缺少策略标识',
  'Missing target_user_id': '缺少目标用户标识',
  'Missing items': '缺少策略项',
  'Missing Authorization header': '登录状态已过期，请重新登录',
  'Invalid or expired token': '登录状态已过期，请重新登录',
  'Invalid value': '数值不合法',
  'Invalid amount': '金额不合法',
  'Invalid id': '记录标识不合法',
  'Invalid status': '状态值不合法',
  'Invalid count': '数量不合法',
  'Invalid force': '参数 force 不合法',
  'Invalid sort_by': '排序字段不合法',
  'Invalid sort_dir': '排序方向不合法',
  'Invalid provider_key': '数据源标识不合法',
  'Invalid include_local': '本地数据开关不合法',
  'Invalid items payload': '策略项格式不合法',
  'Invalid calendar type': '时间范围不合法',
  'Invalid month': '月份不合法',
  'Invalid year or month': '年份或月份不合法',
  'Invalid cash deduction amount': '扣款金额不合法',
  'Invalid cash amount': '回款金额不合法',
  'Insufficient cash balance': '账户余额不足，请更换其他账户',
  'Cash account not found': '现金账户不存在',
  'Failed to add asset': '添加资产失败，请稍后重试',
  'Failed to buy asset': '买入失败，请稍后重试',
  'Failed to buy asset with cash': '现金买入失败，请稍后重试',
  'Failed to sell asset': '卖出失败，请稍后重试',
  'Failed to sell asset to cash': '卖出回款失败，请稍后重试',
  'Failed to modify asset': '调整资产失败，请稍后重试',
  'Failed to delete asset': '删除资产失败，请稍后重试',
  'Failed to undo operation': '撤销失败，请稍后重试',
  'Failed to save snapshot': '保存快照失败，请稍后重试',
  'Failed to take snapshot': '生成快照失败，请稍后重试',
  'Failed to fix snapshots': '修复快照失败，请稍后重试',
  'Restore failed or invalid file': '恢复失败，或备份文件无效',
  'Failed to execute rebind': '执行重绑失败，请稍后重试',
}

function hasChinese(text: string): boolean {
  return /[\u3400-\u9fff]/.test(text)
}

function normalizeMessage(input: unknown): string {
  return String(input || '').trim()
}

export function translateErrorText(input: unknown, fallback = '操作失败，请稍后重试'): string {
  const text = normalizeMessage(input)
  if (!text) return fallback
  if (MESSAGE_TEXT_MAP[text]) return MESSAGE_TEXT_MAP[text]
  if (hasChinese(text)) return text
  if (/^Request failed:\s*\d+$/.test(text)) {
    return MESSAGE_TEXT_MAP[text] || fallback
  }
  if (/[A-Za-z]/.test(text)) {
    return fallback
  }
  return text
}

export function resolveErrorMessage(error: unknown, fallback = '操作失败，请稍后重试'): string {
  const apiError = (error || {}) as Partial<ApiError> & {
    response?: { data?: Record<string, unknown> }
    code?: string
    payload?: Record<string, unknown>
    status?: number
  }
  const payload = apiError.payload || apiError.response?.data || {}
  const code = normalizeMessage(payload.code || apiError.code)
  if (code && CODE_TEXT_MAP[code]) return CODE_TEXT_MAP[code]

  const raw = payload.error || apiError.message || (apiError.status ? `Request failed: ${apiError.status}` : '')
  return translateErrorText(raw, fallback)
}
