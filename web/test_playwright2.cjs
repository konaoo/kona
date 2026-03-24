const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
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
  
  await page.waitForTimeout(1000); 
  
  // Check if modal is visible
  const modalVisible = await page.isVisible('text="搜索资产"');
  console.log('MODAL VISIBLE:', modalVisible);
  
  if (!modalVisible) {
      const display = await page.evaluate(() => {
          const m = document.querySelector('.modal-mask');
          if (m) {
              return { exists: true, display: window.getComputedStyle(m).display, opacity: window.getComputedStyle(m).opacity };
          }
          return { exists: false };
      });
      console.log('MASK STATUS:', display);
  }
  
  await browser.close();
})();
