import { test, expect } from '@playwright/test'

test('调试登录流程', async ({ page }) => {
  // 监听网络请求
  let loginRequestSent = false
  let loginResponseStatus = 0

  page.on('request', request => {
    if (request.url().includes('/api/auth/login')) {
      loginRequestSent = true
      console.log('📤 登录请求已发送:', request.method(), request.url())
    }
  })

  page.on('response', response => {
    if (response.url().includes('/api/auth/login')) {
      loginResponseStatus = response.status()
      console.log('📥 登录响应状态:', response.status())
      response.json().then(data => console.log('📦 登录响应数据:', JSON.stringify(data).substring(0, 200)))
    }
  })

  // 监听控制台错误
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('❌ 控制台错误:', msg.text())
    }
  })

  page.on('pageerror', error => {
    console.log('⚠️ 页面错误:', error.message)
    console.log('   堆栈:', error.stack?.split('\n').slice(0, 5).join('\n'))
  })

  // 导航到登录页
  await page.goto('http://localhost:5174/app/login')
  await page.waitForLoadState('networkidle')

  console.log('✅ 页面已加载')

  // 填写表单
  await page.fill('input[placeholder="请输入用户名"]', 'konae')
  console.log('✅ 用户名已填写')

  await page.fill('input[placeholder="请输入密码"]', 'qq111111')
  console.log('✅ 密码已填写')

  // 检查按钮是否可点击
  const button = page.locator('button.submit-btn')
  const isEnabled = await button.isEnabled()
  console.log('登录按钮是否可点击:', isEnabled)

  // 点击登录按钮
  console.log('🖱️ 准备点击登录按钮...')
  await button.click()
  console.log('✅ 登录按钮已点击')

  // 等待
  await page.waitForTimeout(5000)

  console.log('⏱️ 已等待 5 秒')
  console.log('📍 当前 URL:', page.url())
  console.log('📋 登录请求是否发送:', loginRequestSent)
  console.log('📋 登录响应状态:', loginResponseStatus)

  // 截图
  await page.screenshot({ path: 'screenshots/debug-after-login.png', fullPage: true })
  console.log('📸 截图已保存')

  // 等待更长时间
  await page.waitForTimeout(5000)
  console.log('📍 最终 URL:', page.url())
})
