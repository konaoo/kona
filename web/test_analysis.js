import { chromium, errors } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await page.setViewportSize({ width: 1024, height: 800 });
  await page.goto('http://localhost:5173/#/');
  await page.waitForTimeout(2000);

  console.log("Checking if on landing page...");
  try {
    const enterBtn = await page.waitForSelector('button:has-text("进入网页版")', { timeout: 3000 });
    if (enterBtn) {
      console.log("Clicking enter button to show login dialog...");
      await enterBtn.click();
      await page.waitForTimeout(1500);
      
      console.log("Filling credentials...");
      // Fill the login form based on AppLogin.vue structure
      await page.fill('input[placeholder="请输入用户名/邮箱"]', 'konae');
      await page.fill('input[placeholder="请输入密码"]', 'qq111111');
      await page.click('.login-btn'); // click the submit button

      console.log("Waiting for app navigation...");
      await page.waitForURL('**/app/**', { timeout: 10000 });
      await page.waitForTimeout(2000);
    }
  } catch (err) {
    if (err instanceof errors.TimeoutError) {
      console.log("No login button found or already logged in.");
    } else {
      console.error("Login flow error:", err);
    }
  }

  console.log("Navigating to analysis page...");
  await page.goto('http://localhost:5173/#/app/analysis');
  
  // Wait for the specific new element class to ensure it's loaded
  try {
    await page.waitForSelector('.analysis-page-layout', { timeout: 10000 });
    await page.waitForTimeout(3000); // Give it time to fetch API and render charts/Rankings
    
    await page.screenshot({ path: '/Users/kona/.gemini/antigravity/brain/59e32e7d-d7c4-487e-8b0c-42a0ef7bec84/analysis_page_redesign_final.png', fullPage: true });
    console.log("Screenshot saved!");
  } catch (err) {
    console.error("Analysis page layout not found:", err);
    // Take a screenshot anyway to see where we are stuck
    await page.screenshot({ path: '/Users/kona/.gemini/antigravity/brain/59e32e7d-d7c4-487e-8b0c-42a0ef7bec84/analysis_page_redesign_error.png', fullPage: true });
  }

  await browser.close();
})();
