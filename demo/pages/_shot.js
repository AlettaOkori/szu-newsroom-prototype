const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('file:///d:/Aletta/Okori/Journalism_ShenzhenUniversity/demo/pages/m2-collection.html');
  await page.waitForTimeout(800);
  // scroll to original section
  const orig = await page..original-section;
  if (orig) {
    await orig.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    await page.screenshot({ path: 'd:/Aletta/Okori/Journalism_ShenzhenUniversity/demo/_shot-original.png' });
  }
  // click 原创采录 mode
  await page.click('[data-mode=\"original\"]');
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'd:/Aletta/Okori/Journalism_ShenzhenUniversity/demo/_shot-original-mode.png' });
  // also wait for search to finish on hybrid and screenshot full page
  await page.click('[data-mode=\"hybrid\"]');
  await page.waitForTimeout(3500);
  await page.screenshot({ path: 'd:/Aletta/Okori/Journalism_ShenzhenUniversity/demo/_shot-hybrid-done.png', fullPage: true });
  await browser.close();
})();
