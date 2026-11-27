const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
  page.on('pageerror', e => console.log('PAGE ERROR:', e.message));
  await page.goto('file:///d:/Aletta/Okori/Journalism_ShenzhenUniversity/demo/pages/m6-insights.html');
  await page.waitForTimeout(2600);
  await page.locator('.insights-layout').screenshot({ path: 'd:/Aletta/Okori/Journalism_ShenzhenUniversity/demo/_shot-m6-top.png' });
  await page.locator('.chart-gallery').screenshot({ path: 'd:/Aletta/Okori/Journalism_ShenzhenUniversity/demo/_shot-m6-charts.png' });
  await browser.close();
})();
