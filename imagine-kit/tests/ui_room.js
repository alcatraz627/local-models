// How much height the page leaves for the image on a laptop-sized window.
//
// At 1440 by 800 the image must keep at least 350 px of height at every text size, with nothing in the
// writing box and with two source images in it. A row fails when the box, the header or the foot strip
// has grown into the image's room.
//
// Run: start the kit with the stand-in engine on an EMPTY data folder (see ui_walk.js for the command,
// port 6281), then pass this file to the Playwright MCP's run-code tool. It returns one line per row.
async (page) => {
  const BASE = 'http://127.0.0.1:6281/';
  const out = [];
  const count = () => page.evaluate(async () => (await (await fetch('/api/state')).json()).history.length);
  async function make(words) {
    const before = await count();
    await page.click('#prompt'); await page.keyboard.press('Meta+A'); await page.keyboard.type(words);
    await page.click('#go');
    for (let i = 0; i < 240 && (await count()) <= before; i++) await page.waitForTimeout(250);
    await page.waitForTimeout(1600);
  }
  // The height an image can be drawn at: the stage, less its padding and the image's own 4 px margin.
  const room = () => page.evaluate(() => {
    const st = document.getElementById('stage'), cs = getComputedStyle(st);
    return Math.floor(st.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom) - 4);
  });
  async function rows(what) {
    for (const size of ['sm', 'md', 'lg']) {
      await page.evaluate(s => { document.documentElement.dataset.size = s; }, size);
      await page.waitForTimeout(250);
      const px = await room();
      out.push(`${px >= 350 ? 'ok  ' : 'FAIL'} ${size} text, ${what}: the image has ${px} px of height (350 needed)`);
    }
  }

  await page.setViewportSize({width: 1440, height: 800});
  await page.goto(BASE);
  await page.evaluate(() => localStorage.clear());
  await page.goto(BASE);
  await page.waitForTimeout(1200);

  // An image made from a source has the tallest details row, so measure on one.
  await make('A green teapot on a windowsill');
  await make('Make it evening, warm lamp light from the left');
  await rows('nothing in the box');

  for (const i of [0, 1]) {
    await page.locator('#shelf button').nth(i).click(); await page.waitForTimeout(250);
    await page.click('#more'); await page.waitForTimeout(150);
    await page.click('#reuse'); await page.waitForTimeout(350);
  }
  const sources = await page.locator('#thumbs .thumb').count();
  out.push(`${sources === 2 ? 'ok  ' : 'FAIL'} two source images are in the box (${sources})`);
  await page.locator('#shelf button').nth(1).click(); await page.waitForTimeout(250);
  await rows('two source images in the box');

  // Room is only room if nothing sits on it: the box and the foot strip start below the stage, and the
  // image is held to the stage's height whatever its own size.
  const fit = await page.evaluate(() => {
    const r = s => document.querySelector(s).getBoundingClientRect();
    const stage = r('#stage'), img = document.querySelector('#frame img');
    return {stageBottom: Math.round(stage.bottom), boxTop: Math.round(r('#changeForm').top), footTop: Math.round(r('.foot').top),
            cap: parseFloat(getComputedStyle(img).maxHeight), stageHeight: Math.round(stage.height)};
  });
  out.push(`${fit.boxTop >= fit.stageBottom && fit.footTop >= fit.stageBottom ? 'ok  ' : 'FAIL'} the box and the foot strip start below the image's room (${JSON.stringify(fit)})`);
  out.push(`${fit.cap > 0 && fit.cap <= fit.stageHeight ? 'ok  ' : 'FAIL'} the image is held to its room's height (cap ${fit.cap} px, room ${fit.stageHeight} px)`);

  return `ok=${out.filter(l => l.startsWith('ok')).length} fail=${out.filter(l => l.startsWith('FAIL')).length}\n` + out.join('\n');
}
