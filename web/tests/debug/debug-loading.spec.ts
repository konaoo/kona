import { test, expect } from '@playwright/test'

test('调试加载状态', async ({ page }) => {
  const consoleErrors: string[] = []
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text())
    }
  })

  page.on('pageerror', error => {
    console.log('⚠️ 页面错误:', error.message)
  })

  await page.goto('http://localhost:5174/app/login')
  await page.waitForLoadState('networkidle')

  await page.fill('input[placeholder="请输入用户名"]', 'konae')
  await page.fill('input[placeholder="请输入密码"]', 'qq111111')
  await page.click('button.submit-btn')

  await page.waitForURL('http://localhost:5174/app/home', { timeout: 10000 })
  await page.waitForLoadState('networkidle')

  console.log('📍 当前 URL:', page.url())

  // 等待并检查加载状态
  await page.waitForTimeout(10000)

  const stillLoading = await page.evaluate(() => {
    const loadingText = Array.from(document.querySelectorAll('*')).find(el => el.textContent?.includes('加载中'))
    return !!loadingText
  })

  console.log('📊 10秒后仍在加载:', stillLoading)
  console.log('❌ 控制台错误:', consoleErrors)

  // 检查网络请求
  const networkErrors = await page.evaluate(() => {
    return (window as any).networkErrors || []
  })
  console.log('🌐 网络错误:', networkErrors)
})
