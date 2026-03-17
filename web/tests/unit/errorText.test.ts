import { describe, expect, it } from 'vitest'
import { resolveErrorMessage, translateErrorText } from '../../src/shared/errorText'

describe('errorText', () => {
  it('会把通用英文状态错误翻成中文', () => {
    expect(translateErrorText('Request failed: 500')).toBe('服务器开小差了，请稍后重试')
    expect(translateErrorText('Failed to fetch')).toBe('网络连接失败，请检查网络后重试')
  })

  it('会优先按后端错误码翻译', () => {
    expect(resolveErrorMessage({
      payload: {
        code: 'INSUFFICIENT_CASH',
        error: 'Insufficient cash balance',
      },
    })).toBe('账户余额不足，请更换其他账户')
  })

  it('会把缺少参数这类英文提示翻成中文', () => {
    expect(resolveErrorMessage({
      payload: {
        error: 'Missing required fields',
      },
    })).toBe('缺少必填参数')
  })
})
