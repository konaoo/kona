import { test, expect } from '@playwright/test'

test('验证首页整体视觉效果', async ({ page }) => {
  // 导航到登录页
  await page.goto('http://localhost:5174/app/login')
  await page.waitForLoadState('networkidle')

  // 填写表单并登录
  await page.fill('input[placeholder="请输入用户名"]', 'konae')
  await page.fill('input[placeholder="请输入密码"]', 'qq111111')
  await page.click('button.submit-btn')

  // 等待跳转到首页
  await page.waitForURL('http://localhost:5174/app/home', { timeout: 10000 })
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(10000) // Wait longer for content to fully load

  console.log('📍 当前 URL:', page.url())

  // 检查页面结构
  const pageContent = await page.content()
  console.log('✅ 页面已加载')

  // 检查关键元素是否存在
  const elements = await page.evaluate(() => {
    return {
      hasPageDiv: !!document.querySelector('.page'),
      hasHomeHero: !!document.querySelector('.home-hero'),
      hasHeroVal: !!document.querySelector('.hero-val'),
      hasMarketPill: !!document.querySelector('.market-pill'),
      hasPulseDot: !!document.querySelector('.pulse-dot'),
      hasAcctMini: !!document.querySelector('.acct-mini'),
      hasTabs: !!document.querySelector('.tabs'),
      hasTab: !!document.querySelector('.tab'),
      hasHoldingList: !!document.querySelector('.holding-list'),
      hasHoldingRow: !!document.querySelector('.holding-row'),
      hasHIcon: !!document.querySelector('.h-icon'),
      hasProgressWrap: !!document.querySelector('.progress-wrap'),
      hasBadge: !!document.querySelector('.badge'),
      hasTag: !!document.querySelector('.tag'),
    }
  })

  console.log('🔍 关键元素检查:')
  console.log(`   .page: ${elements.hasPageDiv ? '✅' : '❌'}`)
  console.log(`   .home-hero: ${elements.hasHomeHero ? '✅' : '❌'}`)
  console.log(`   .hero-val: ${elements.hasHeroVal ? '✅' : '❌'}`)
  console.log(`   .market-pill: ${elements.hasMarketPill ? '✅' : '❌'}`)
  console.log(`   .pulse-dot: ${elements.hasPulseDot ? '✅' : '❌'}`)
  console.log(`   .acct-mini: ${elements.hasAcctMini ? '✅' : '❌'}`)
  console.log(`   .tabs: ${elements.hasTabs ? '✅' : '❌'}`)
  console.log(`   .tab: ${elements.hasTab ? '✅' : '❌'}`)
  console.log(`   .holding-list: ${elements.hasHoldingList ? '✅' : '❌'}`)
  console.log(`   .holding-row: ${elements.hasHoldingRow ? '✅' : '❌'}`)
  console.log(`   .h-icon: ${elements.hasHIcon ? '✅' : '❌'}`)
  console.log(`   .progress-wrap: ${elements.hasProgressWrap ? '✅' : '❌'}`)
  console.log(`   .badge: ${elements.hasBadge ? '✅' : '❌'}`)
  console.log(`   .tag: ${elements.hasTag ? '✅' : '❌'}`)

  // 验证所有关键元素都存在
  expect(elements.hasPageDiv).toBe(true)
  expect(elements.hasHomeHero).toBe(true)
  expect(elements.hasHeroVal).toBe(true)
  expect(elements.hasMarketPill).toBe(true)
  expect(elements.hasPulseDot).toBe(true)
  expect(elements.hasAcctMini).toBe(true)
  expect(elements.hasTabs).toBe(true)
  expect(elements.hasTab).toBe(true)

  // 检查文字内容
  const heroText = await page.locator('.hero-val').textContent()
  console.log(`💰 总资产显示: ${heroText}`)
  expect(heroText).toBeTruthy()

  // 检查市场状态标签
  const marketPillText = await page.locator('.market-pill').textContent()
  console.log(`📊 市场标签: ${marketPillText}`)
  expect(marketPillText).toContain('市场开放中')

  // 检查标签页
  const tabs = await page.locator('.tab').allTextContents()
  console.log(`🏷️ 标签页: ${tabs.join(', ')}`)
  expect(tabs.length).toBeGreaterThan(0)

  // 最终截图
  await page.screenshot({
    path: 'screenshots/homepage-visual-final.png',
    fullPage: true
  })
  console.log('📸 最终截图已保存: screenshots/homepage-visual-final.png')

  console.log('✅ 视觉效果验证完成')
})
