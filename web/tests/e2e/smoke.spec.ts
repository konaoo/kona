import { expect, test } from '@playwright/test'

test('登录后关键页面可正常打开', async ({ page }) => {
  const consoleErrors: string[] = []
  const pageErrors: string[] = []

  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text())
    }
  })
  page.on('pageerror', (error) => {
    pageErrors.push(error.message)
  })

  const homeHistoryResponse = page.waitForResponse((response) =>
    response.url().includes('/api/history?days=5000'),
  )

  await page.goto('/app/login')
  await page.getByPlaceholder('请输入用户名').fill('konae')
  await page.getByPlaceholder('请输入密码').fill('qq111111')
  await page.locator('button.submit-btn').click()

  await expect(page).toHaveURL(/\/app\/home$/)
  await expect(page.getByText('我的资产')).toBeVisible()
  await expect(page.locator('.market-strip')).toBeVisible()

  const historyResponse = await homeHistoryResponse
  expect(historyResponse.headers()['x-request-id']).toBeTruthy()

  await page.getByRole('navigation').locator('.nav-item').filter({ hasText: '投资' }).first().click()
  await expect(page).toHaveURL(/\/app\/invest$/)
  await expect(page.getByText('资产分布')).toBeVisible()

  await page.getByRole('navigation').locator('.nav-item').filter({ hasText: '分析' }).first().click()
  await expect(page).toHaveURL(/\/app\/analysis$/)
  await expect(page.getByText('收益日历')).toBeVisible()

  expect(consoleErrors).toEqual([])
  expect(pageErrors).toEqual([])
})
