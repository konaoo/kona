const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  
  // 捕获 API 响应
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/')) {
      console.log(`API RESPONSE [${response.request().method()}] ${url} status:`, response.status());
      if (url.includes('/api/cash_assets')) {
        try {
          const text = await response.text();
          console.log(`API RESPONSE BODY ${url}:`, text);
        } catch (e) {
          console.log('Error reading response body:', e);
        }
      }
    }
  });

  // 1. 去线上登录页
  console.log('Navigating to online login page...');
  await page.goto('https://kakalog.fun/app/login');
  
  // 2. 输入登录凭证
  console.log('Logging in...');
  await page.fill('input[placeholder="请输入用户名"]', 'konae');
  await page.fill('input[placeholder="请输入密码"]', 'qq111111');
  await page.click('button.submit-btn');
  
  // 3. 等待跳转到首页
  console.log('Waiting for redirect to home...');
  await page.waitForURL('**/app/home', { timeout: 10000 });
  console.log('Successfully logged in online!');
  
  // 4. 直接导航到中远海控 (sh601919) 的详情页
  const detailUrl = 'https://kakalog.fun/app/asset/sh601919';
  console.log(`Navigating directly to online detail page: ${detailUrl}`);
  await page.goto(detailUrl, { waitUntil: 'networkidle' });
  
  // 5. 点击“加仓”
  console.log('Clicking 加仓 button...');
  await page.waitForSelector('button:has-text("加仓")');
  await page.click('button:has-text("加仓")');
  
  // 6. 等待交易弹窗展示出来，并且点击资金账户选择器
  console.log('Waiting for modal...');
  await page.waitForSelector('.acct-trigger', { timeout: 5000 });
  
  // 截图 1：点击前
  const screenshotDir = '/Users/kona/Desktop/kaka/kona_repo/web';
  await page.screenshot({ path: path.join(screenshotDir, 'online_modal_before_click.png') });
  console.log('Screenshot saved: online_modal_before_click.png');
  
  console.log('Clicking acct-trigger...');
  await page.click('.acct-trigger');
  
  // 等待下拉框展开
  await page.waitForTimeout(1000);
  
  // 截图 2：点击后
  await page.screenshot({ path: path.join(screenshotDir, 'online_modal_after_click.png') });
  console.log('Screenshot saved: online_modal_after_click.png');
  
  // 打印当前的账户列表 DOM 内容
  const dropdownHtml = await page.evaluate(() => {
    const el = document.querySelector('.acct-dropdown');
    return el ? el.innerHTML : 'Not found .acct-dropdown';
  });
  console.log('Dropdown inner HTML:', dropdownHtml);
  
  await browser.close();
})();
