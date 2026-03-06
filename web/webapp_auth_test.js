import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  await page.goto('http://localhost:5173/app/login');
  
  // Wait for input fields and fill them
  await page.waitForSelector('input[placeholder="请输入用户名"]');
  await page.fill('input[placeholder="请输入用户名"]', 'konae');
  
  await page.waitForSelector('input[placeholder="请输入密码"]');
  await page.fill('input[placeholder="请输入密码"]', 'qq111111');
  
  // Take a screenshot of the filled form
  await page.screenshot({ path: '/Users/kona/.gemini/antigravity/brain/38019e22-1209-43a6-8860-387fc6417935/debug_login_step_1.png' });
  
  // Click the submit button
  await page.click('button.submit-btn');
  
  // Wait a few seconds to see the result
  await page.waitForTimeout(3000);
  
  // Take screenshot of the result (error msg or redirected page)
  await page.screenshot({ path: '/Users/kona/.gemini/antigravity/brain/38019e22-1209-43a6-8860-387fc6417935/debug_login_step_2.png', fullPage: true });
  
  await browser.close();
})();
