import { test, expect, Page } from '@playwright/test'

test.describe('登录测试', () => {
  test('应该成功登录并跳转到首页', async ({ page }) => {
    // 监听控制台消息
    const consoleErrors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text())
      }
    })

    // 监听页面错误
    const pageErrors: Array<{ error: Error; stack?: string }> = []
    page.on('pageerror', error => {
      pageErrors.push({ error, stack: error.stack })
    })

    // 导航到登录页
    await page.goto('http://localhost:5173/app/login')

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 截图 - 登录页
    await page.screenshot({ path: 'screenshots/login-page.png' })
    console.log('✅ 登录页截图已保存: screenshots/login-page.png')

    // 填写表单
    await page.fill('input[placeholder="请输入用户名"]', 'konae')
    await page.fill('input[placeholder="请输入密码"]', 'qq111111')

    // 点击登录按钮
    await page.click('button.submit-btn')

    // 等待一下让请求发送
    await page.waitForTimeout(3000)

    // 检查是否有错误消息
    const errorElement = await page.locator('.input-error.visible').first()
    const hasError = await errorElement.count() > 0
    if (hasError) {
      const errorText = await errorElement.textContent()
      console.log('❌ 登录错误:', errorText)
    }

    // 等待导航或错误
    try {
      await page.waitForURL('http://localhost:5173/app/home', { timeout: 10000 })
    } catch (e) {
      // 截图当前状态
      await page.screenshot({ path: 'screenshots/after-login-click.png', fullPage: true })
      console.log('登录后 URL:', page.url())
      console.log('当前页面标题:', await page.title())

      // 检查按钮状态
      const buttonText = await page.locator('button.submit-btn').textContent()
      console.log('登录按钮文字:', buttonText)

      // 检查控制台错误
      if (consoleErrors.length > 0) {
        console.log('控制台错误:', consoleErrors)
      }

      throw e
    }

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 截图 - 首页
    await page.screenshot({ path: 'screenshots/home-page.png', fullPage: true })
    console.log('✅ 首页截图已保存: screenshots/home-page.png')

    // 检查控制台错误
    if (consoleErrors.length > 0) {
      console.error('❌ 发现控制台错误:')
      consoleErrors.forEach(err => console.error(`  - ${err}`))
    } else {
      console.log('✅ 没有控制台错误')
    }

    // 检查页面错误
    if (pageErrors.length > 0) {
      console.error('❌ 发现页面错误:')
      pageErrors.forEach((err, idx) => {
        console.error(`  错误 ${idx + 1}: ${err.error.message}`)
        if (err.stack) {
          console.error(`    堆栈: ${err.stack}`)
        }
      })
    } else {
      console.log('✅ 没有页面错误')
    }

    // 获取页面标题
    const title = await page.title()
    console.log(`页面标题: ${title}`)

    // 检查页面内容
    const content = await page.content()
    console.log(`页面 HTML 长度: ${content.length}`)

    // 检查关键元素
    const shell = await page.locator('.layout').count()
    const sidebar = await page.locator('.sidebar').count()
    const mainContent = await page.locator('.main').count()

    console.log(`Shell 元素: ${shell > 0 ? '✅ 存在' : '❌ 缺失'}`)
    console.log(`Sidebar 元素: ${sidebar > 0 ? '✅ 存在' : '❌ 缺失'}`)
    console.log(`主内容区: ${mainContent > 0 ? '✅ 存在' : '❌ 缺失'}`)

    // 等待一下以便观察
    await page.waitForTimeout(3000)
  })
})
