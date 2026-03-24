const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  
  // Login
  await page.goto('http://localhost:5173');
  await page.evaluate(() => {
    localStorage.setItem('kona_web_access_token', 'mock_token');
    localStorage.setItem('kona_web_user', JSON.stringify({id: 'test', username: 'test'}));
  });
  
  await page.goto('http://localhost:5173/app/invest', {waitUntil: 'networkidle'});
  
  // Wait for the button and click
  await page.waitForSelector('button:has-text("添加资产")');
  await page.click('button:has-text("添加资产")');
  
  await page.waitForTimeout(2000); // Wait to see if it closes
  await page.screenshot({ path: 'modal_test.png' });
  await browser.close();
})();
