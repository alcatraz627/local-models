// One real render of each kind, driven through the studio page with real clicks and typing:
// a new image, a change to it, a marked-area change, and a two-source combine.
//
// Run: start the kit with the REAL engine (no IMAGINE_KIT_FAKE) on an EMPTY data folder, port 6281, then pass
// this file to the Playwright MCP's run-code tool. It returns each render's seconds and size from the kit's
// own record, to compare with the Mac baseline (about 11 s new, 19 s change, 18 s marked area, 30 s combine).
async (page) => {
  const BASE = 'http://127.0.0.1:6281/';
  const state = () => page.evaluate(async () => (await (await fetch('/api/state')).json()));
  async function landed(n, ms = 240000) {
    const t = Date.now();
    while (Date.now() - t < ms) {
      const s = await state();
      const failed = s.jobs.find(j => j.state === 'failed');
      if (failed) return {error: failed.error};
      if (s.history.length >= n && !s.jobs.some(j => j.state === 'queued' || j.state === 'running')) { await page.waitForTimeout(1500); return s.history[0]; }
      await page.waitForTimeout(1000);
    }
    return {error: 'timed out'};
  }
  const out = [];
  const note = (kind, r) => out.push(r.error ? `FAIL ${kind}: ${JSON.stringify(r.error)}` : `ok   ${kind}: image ${r.id}, ${r.secs} s, ${r.width}x${r.height}, mode ${r.mode}${r.region ? ', area' : ''}`);
  const type = async words => { await page.click('#prompt'); await page.keyboard.press('Meta+A'); await page.keyboard.type(words); };

  await page.setViewportSize({width: 1440, height: 900});
  await page.goto(BASE); await page.evaluate(() => localStorage.clear()); await page.goto(BASE); await page.waitForTimeout(1500);

  await type('A ceramic mug of coffee on a wooden table, morning light from a window');
  await page.click('#go'); note('new image', await landed(1));

  await type('Make the mug deep blue. Keep the table, the light and the framing.');
  await page.click('#go'); note('change', await landed(2));

  await page.click('#markBtn');
  const box = await (await page.$('#frame')).boundingBox();
  await page.mouse.move(box.x + box.width * .55, box.y + box.height * .15);
  await page.mouse.down(); await page.mouse.move(box.x + box.width * .9, box.y + box.height * .45, {steps: 8}); await page.mouse.up();
  await type('Add a small potted plant here');
  await page.click('#go'); note('marked area', await landed(3));

  // Two sources: image 1 and image 2 into the box, then combine.
  await page.click('#shelf button[data-id="1"]'); await page.click('#more'); await page.click('#reuse');
  await page.click('#shelf button[data-id="2"]'); await page.click('#more'); await page.click('#reuse');
  await type('Put both mugs side by side on the same table');
  await page.click('#go'); note('two-source combine', await landed(4));

  await page.screenshot({path: '/Users/alcatraz627/Code/local-models/assets/studio-direction/shots/real-page-after-renders.png'});
  return out.join('\n');
}
