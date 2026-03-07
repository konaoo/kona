const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  // Track console and errors
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  
  // Set auth token to bypass login redirect
  await page.goto('http://localhost:5173');
  await page.evaluate(() => {
    localStorage.setItem('kaka_token', 'mock_token');
    localStorage.setItem('kaka_refresh', 'mock_refresh');
  });
  
  await page.goto('http://localhost:5173/app/invest', {waitUntil: 'networkidle0'});
  await page.click('text="添加资产"');
  await page.waitForTimeout(1000);
  await browser.close();
})();
