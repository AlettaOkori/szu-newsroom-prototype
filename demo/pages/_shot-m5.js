const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
  page.on('pageerror', e => console.log('PAGE ERROR:', e.message));
  await page.goto('file:///d:/Aletta/Okori/Journalism_ShenzhenUniversity/demo/pages/m5-channels.html');
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'd:/Aletta/Okori/Journalism_ShenzhenUniversity/demo/_shot-m5-current.png' });
  await page.click('#channelAction');
  await page.waitForTimeout(2800);
  for (const ch of ['weibo', 'video', 'xhs', 'toutiao']) {
    await page.click(`.channel-item[data-channel="${ch}"]`);
    await page.waitForTimeout(350);
    await page.screenshot({ path: `d:/Aletta/Okori/Journalism_ShenzhenUniversity/demo/_shot-m5-${ch}.png` });
  }
  await page.click('#generateEn');
  await page.waitForTimeout(1200);
  await page.click('#runDistributionCheck');
  await page.waitForTimeout(2200);
  await page.screenshot({ path: 'd:/Aletta/Okori/Journalism_ShenzhenUniversity/demo/_shot-m5-ready.png' });
  await page.click('#channelAction');
  await page.waitForTimeout(1600);
  console.log('after publish url:', page.url());
  await browser.close();
})();
