// The header's and the writing box's controls, pressed with a real mouse and keyboard.
//
// Covers what the walk does not press: the model button and its panel, the View menu (text size and
// theme), thread delete and what it leaves behind, one panel open at a time, where focus goes when a
// panel closes, the writing box at an in-between width, and a failed render not moving the image.
//
// Run: start the kit with the stand-in engine on an EMPTY data folder (see ui_walk.js for the command,
// port 6281), then pass this file to the Playwright MCP's run-code tool. It returns one line per row.
async (page) => {
  const BASE = 'http://127.0.0.1:6281/';
  const out = [];
  const row = (ok, name, got) => out.push(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok ? '' : ' :: ' + JSON.stringify(got)}`);
  const tap = sel => page.click(sel, {timeout: 4000}).catch(() => out.push(`FAIL could not press ${sel}`));
  const count = () => page.evaluate(async () => (await (await fetch('/api/state')).json()).history.length);
  async function make(words) {
    const before = await count();
    await tap('#prompt'); await page.keyboard.press('Meta+A'); await page.keyboard.type(words);
    await tap('#go');
    for (let i = 0; i < 240 && (await count()) <= before; i++) await page.waitForTimeout(250);
    await page.waitForTimeout(1600);
  }
  const shown = sel => page.evaluate(s => { const e = document.querySelector(s); return !!e && !e.hidden && e.offsetParent !== null; }, sel);
  const text = sel => page.evaluate(s => document.querySelector(s)?.textContent.replace(/\s+/g, ' ').trim() ?? null, sel);
  const focus = () => page.evaluate(() => document.activeElement?.id || document.activeElement?.tagName);

  await page.setViewportSize({width: 1440, height: 800});
  await page.goto(BASE);
  await page.evaluate(() => localStorage.clear());
  await page.goto(BASE);
  await page.waitForTimeout(1200);

  // Two threads. The second holds an image made from a source, so it has a "Made from" thumbnail.
  await make('An older idea');
  await tap('#newThread');
  await make('A green teapot on a windowsill');
  await make('Make it evening');
  const threads = () => page.locator('#threads button[data-t]').count();

  // The View menu: it opens on a press, and its buttons do what they say.
  await tap('#viewBtn');
  row(await shown('#viewPop'), 'the View button opens its panel');
  await tap('.size button[data-size="lg"]');
  row(await page.evaluate(() => document.documentElement.dataset.size) === 'lg', 'the Large button sets large text');
  if (!(await shown('#viewPop'))) await tap('#viewBtn');
  const theme = await page.evaluate(() => document.documentElement.dataset.theme);
  await tap('#theme');
  row(await page.evaluate(() => document.documentElement.dataset.theme) !== theme, 'the theme button, pressed where it is shown, switches light and dark');
  if (!(await shown('#viewPop'))) await tap('#viewBtn');
  await tap('.size button[data-size="sm"]');
  await page.keyboard.press('Escape');

  // The model button: it opens a panel, and a row in it picks the model.
  await tap('#subjectClear');
  await tap('#modelBtn');
  row(await shown('#modelPop'), 'the model button opens its panel');
  const before = await text('#whereSay');
  await tap('#modelList .model-row[aria-pressed="false"]');
  const after = await text('#whereSay');
  row(after !== before && !(await shown('#modelPop')), 'picking a model row changes the model and closes the panel', {before, after});
  row(await focus() === 'modelBtn', 'focus is on the model button after a pick', await focus());
  await tap('#modelBtn');
  await tap('#modelList .model-row[data-m="klein"]');
  await tap('#modelBtn');
  await page.keyboard.press('Tab');
  await page.keyboard.press('Escape');
  row(!(await shown('#modelPop')) && await focus() === 'modelBtn', 'Escape closes the model panel and gives focus back to its button', await focus());
  await tap('#modeChange');

  // One thing open at a time.
  await tap('#more');
  await tap('#modelBtn');
  row((await shown('#modelPop')) && !(await shown('#morePop')), 'opening the model panel closes the More menu');
  await tap('#more');
  row((await shown('#morePop')) && !(await shown('#modelPop')), 'opening the More menu closes the model panel');
  await page.keyboard.press('Escape');

  // The writing box at an in-between width: the words keep room to be read.
  await page.evaluate(() => { document.documentElement.dataset.size = 'lg'; });
  for (const w of [880, 960, 1024]) {
    await page.setViewportSize({width: w, height: 800}); await page.waitForTimeout(250);
    const px = await page.evaluate(() => Math.round(document.getElementById('prompt').getBoundingClientRect().width));
    row(px >= 240, `at ${w} wide with large text the words have ${px} px of width (240 needed)`);
  }
  await page.evaluate(() => { document.documentElement.dataset.size = 'sm'; });
  await page.setViewportSize({width: 1440, height: 800}); await page.waitForTimeout(250);

  // A failure shown in the foot strip does not move the image.
  const top = () => page.evaluate(() => Math.round(document.querySelector('#frame img').getBoundingClientRect().top));
  const t0 = await top();
  await page.evaluate(() => showError({ok: false, message: 'The model failed before it finished.', fix: 'A test asked for this failure.'}));
  await page.waitForTimeout(250);
  const t1 = await top();
  row(t1 === t0 && await shown('#failClose'), 'a failure in the foot strip leaves the image where it was', {t0, t1});
  await tap('#failClose');

  // Thread delete: the first press only arms it, and moving away disarms it.
  const had = await threads();
  await tap('#delThread');
  row(await threads() === had && /Delete all 2 images/.test(await text('#delThread')), 'the first press on delete only asks, naming the count', await text('#delThread'));
  await tap('#threads button[data-t]:not([aria-current=true])');
  await tap('#shelf button');
  await tap('#threads button[data-t]:not([aria-current=true])');
  row(!(await page.evaluate(() => document.getElementById('delThread').classList.contains('armed'))), 'leaving the thread and coming back disarms its delete');

  // Thread delete: nothing of the deleted thread is left on the page.
  await tap('#detail button[data-src]');
  await tap('#more'); await tap('#reuse');
  row(await page.locator('#thumbs .thumb').count() === 1 && /A source of/.test(await text('#frame .tag') || ''), 'setup: a source is on the stage and in the box');
  await tap('#delThread'); await tap('#delThread');
  await page.waitForTimeout(1500);
  const left = {threads: await threads(), tag: await text('#frame .tag'), go: await text('#go'), thumbs: await page.locator('#thumbs .thumb').count(),
                current: await page.evaluate(() => document.querySelector('#shelf [aria-current=true]')?.dataset.id ?? null)};
  row(left.threads === had - 1 && left.tag === null && left.go === `Change image ${left.current}`, 'after a thread delete the next thread shows its own image, with no source on the stage', left);

  // An image of the deleted thread is dropped from the box with it.
  await tap('#newThread');
  await make('A kite over a beach');
  await tap('#more'); await tap('#reuse');
  const inBox = await page.locator('#thumbs .thumb').count();
  await tap('#delThread'); await tap('#delThread');
  await page.waitForTimeout(1500);
  row(inBox === 1 && await page.locator('#thumbs .thumb').count() === 0, 'an image of the deleted thread leaves the writing box too', {inBox, now: await page.locator('#thumbs .thumb').count()});

  return `ok=${out.filter(l => l.startsWith('ok')).length} fail=${out.filter(l => l.startsWith('FAIL')).length}\n` + out.join('\n');
}
