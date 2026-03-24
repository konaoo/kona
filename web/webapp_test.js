import { chromium } from 'playwright';
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:5175/app/home');
  // Wait a moment for rendering and API calls
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/Users/kona/.gemini/antigravity/brain/38019e22-1209-43a6-8860-387fc6417935/homepage_replica_check.png', fullPage: true });
  await browser.close();
})();
