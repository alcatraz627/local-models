// Shoots the real studio page (kit on 6281 with the real render set) in the states worth reading:
// each thread shape at 1440x900 dark, light, a laptop-height window, 820 and 390, and medium text.
async (page) => {
  const OUT = '/Users/alcatraz627/Code/local-models/assets/studio-direction/shots/real-';
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  const go = async (w, h, q, tag) => {
    await page.setViewportSize({width: w, height: h});
    await page.goto('http://127.0.0.1:6281/?' + q);
    await page.waitForTimeout(1300);
    await page.screenshot({path: `${OUT}${tag}.png`});
  };
  await page.goto('http://127.0.0.1:6281/'); await page.evaluate(() => localStorage.clear());
  await go(1440, 900, 'theme=dark&open=8', 'square-dark');
  await go(1440, 900, 'theme=light&open=3', 'portrait-light');
  await go(1440, 900, 'theme=dark&open=5', 'wide-dark');
  await go(1440, 800, 'theme=dark&open=3', 'portrait-1440x800');
  await go(1440, 900, 'theme=dark&open=5&menu=more', 'more-dark');
  await go(1440, 900, 'theme=dark&open=3&size=md', 'md-dark');
  await go(820, 1100, 'theme=light&open=5', 'tablet-light');
  await go(390, 844, 'theme=dark&open=3', 'phone-dark');
  await go(1440, 900, 'theme=dark&new=1', 'new-thread-dark');
  return errs.length ? errs.join('\n') : 'no page errors';
}
