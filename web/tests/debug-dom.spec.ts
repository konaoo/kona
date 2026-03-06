import { test, expect } from '@playwright/test'

test('调试DOM结构', async ({ page }) => {
  await page.goto('http://localhost:5174/app/login')
  await page.waitForLoadState('networkidle')

  await page.fill('input[placeholder="请输入用户名"]', 'konae')
  await page.fill('input[placeholder="请输入密码"]', 'qq111111')
  await page.click('button.submit-btn')

  await page.waitForURL('http://localhost:5174/app/home', { timeout: 10000 })
  await page.waitForLoadState('networkidle')

  // 等待更长时间以确保数据加载完成
  await page.waitForTimeout(5000)

  // 检查是否还在加载状态
  const isLoading = await page.evaluate(() => {
    const loadingText = Array.from(document.querySelectorAll('*')).find(el => el.textContent?.includes('加载中'))
    return !!loadingText
  })
  console.log('📊 是否在加载状态:', isLoading)

  // 检查DOM结构
  const domInfo = await page.evaluate(() => {
    const captureArea = document.getElementById('capture-area')
    if (!captureArea) {
      // 检查整个body的内容
      return {
        error: 'No capture-area found',
        bodyHTML: document.body.innerHTML.substring(0, 500)
      }
    }

    const children = Array.from(captureArea.children)
    return {
      captureAreaExists: true,
      childCount: children.length,
      firstChildClass: children[0]?.className || 'no-class',
      firstChildTag: children[0]?.tagName || 'no-tag',
      firstChildHTML: children[0]?.outerHTML?.substring(0, 200) || 'no-html',
      allClasses: Array.from(captureArea.querySelectorAll('[class]')).map(el => el.className).slice(0, 10)
    }
  })

  console.log('🔍 DOM信息:', JSON.stringify(domInfo, null, 2))
})
