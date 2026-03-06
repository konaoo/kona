import { test, expect } from '@playwright/test'

test('验证首页颜色是否与参考设计匹配', async ({ page }) => {
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
  await page.waitForTimeout(3000) // 等待内容完全渲染

  // 截图 - 完整页面
  await page.screenshot({ path: 'screenshots/homepage-colors-final.png', fullPage: true })
  console.log('✅ 首页截图已保存: screenshots/homepage-colors-final.png')

  // 验证关键CSS变量是否正确加载
  const styles = await page.evaluate(() => {
    const root = document.documentElement
    const computed = getComputedStyle(root)
    return {
      backgroundColor: computed.getPropertyValue('--bg').trim(),
      textColor: computed.getPropertyValue('--text').trim(),
      greenColor: computed.getPropertyValue('--green').trim(),
      redColor: computed.getPropertyValue('--red').trim(),
      blueColor: computed.getPropertyValue('--blue').trim(),
      goldColor: computed.getPropertyValue('--gold').trim(),
    }
  })

  console.log('🎨 CSS 变量值:')
  console.log(`   --bg: ${styles.backgroundColor}`)
  console.log(`   --text: ${styles.textColor}`)
  console.log(`   --green: ${styles.greenColor}`)
  console.log(`   --red: ${styles.redColor}`)
  console.log(`   --blue: ${styles.blueColor}`)
  console.log(`   --gold: ${styles.goldColor}`)

  // 验证颜色值是否正确
  expect(styles.backgroundColor).toBe('#0a0b0e')
  expect(styles.textColor).toBe('#e4e5ea')
  expect(styles.greenColor).toBe('#3ecf82')
  expect(styles.redColor).toBe('#f05a55')
  expect(styles.blueColor).toBe('#5b8def')
  expect(styles.goldColor).toBe('#d4af64')

  console.log('✅ 所有CSS变量值验证通过')

  // 检查页面主体背景色
  const bodyBg = await page.evaluate(() => {
    return getComputedStyle(document.body).backgroundColor
  })
  console.log(`📄 页面背景色: ${bodyBg}`)

  // 检查关键元素的文本颜色
  const heroTextColor = await page.evaluate(() => {
    const heroVal = document.querySelector('.hero-val')
    return heroVal ? getComputedStyle(heroVal).color : null
  })
  console.log(`💰 Hero文本颜色: ${heroTextColor}`)

  console.log('✅ 颜色验证完成')
})
