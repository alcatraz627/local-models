// Shoots each studio direction at 1440x900 in dark and light, the bicycle and harbour threads,
// and at 390 in dark. Returns any page errors.
async (page) => {
  const OUT = '/Users/alcatraz627/Code/local-models/assets/studio-direction/shots/';
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  const names = ['canvas', 'sheet', 'studio'];
  for (const n of names) {
    for (const [w, h, theme, extra, tag] of [
      [1440, 900, 'dark', 'thread=0', 'dark'], [1440, 900, 'light', 'thread=0', 'light'],
      [1440, 900, 'dark', 'thread=1', 'wide-dark'], [1440, 900, 'dark', 'thread=2&mode=new', 'new-dark'],
      [390, 844, 'dark', 'thread=0', 'phone-dark']]) {
      await page.setViewportSize({width: w, height: h});
      const r = await page.goto(`http://127.0.0.1:6284/${n}.html?theme=${theme}&${extra}`).catch(e => null);
      if (!r || r.status() !== 200) { errs.push(`${n}: not served`); continue; }
      await page.waitForTimeout(500);
      await page.screenshot({path: `${OUT}${n}-${tag}.png`});
    }
  }
  return errs.length ? errs.join('\n') : 'no page errors';
}
