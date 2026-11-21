// What happens to the reader when a render finishes while they are doing something else.
//
// Each case starts a render, does something with real mouse and keyboard input while it draws, waits for
// it to land, and checks what is on screen. The rule under test: a finished render never changes the
// open thread, the image on the stage, what the writing box is about, a marked area, a drag or a name
// being typed. The image the reader was waiting for is offered as "Image N is ready" instead.
//
// Run: start the kit with the stand-in engine on an EMPTY data folder (see ui_walk.js for the command,
// port 6281), then pass this file's text to the Playwright MCP's run-code tool. It returns one line per
// row, "ok ..." or "FAIL ...", and never stops at the first failure.
async (page) => {
  const BASE = 'http://127.0.0.1:6281/';
  const out = [];
  const row = (ok, name, got) => out.push(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok ? '' : ' :: ' + JSON.stringify(got)}`);
  // A press on a control that is not there is a failed row, never the end of the run.
  const tap = (sel, opt) => page.click(sel, {timeout: 4000, ...opt}).catch(() => out.push(`FAIL could not press ${sel}`));
  const count = () => page.evaluate(async () => (await (await fetch('/api/state')).json()).history.length);
  const idle = () => page.evaluate(async () => (await (await fetch('/api/state')).json()).jobs.every(j => j.state !== 'queued' && j.state !== 'running'));
  async function until(fn, ms = 60000) {
    const t = Date.now();
    while (Date.now() - t < ms) { if (await fn()) return true; await page.waitForTimeout(250); }
    return false;
  }
  // Waits for n more images, then for the page's own refresh to have seen them.
  async function landed(before, n = 1) { const ok = await until(async () => (await count()) >= before + n); await page.waitForTimeout(1600); return ok; }
  const screen = () => page.evaluate(() => ({
    title: document.querySelector('#head h2')?.textContent ?? null,
    chip: document.getElementById('subject').hidden ? null : document.getElementById('subjectSay').textContent,
    go: document.getElementById('go').textContent.trim(),
    prompt: document.getElementById('prompt').value,
    current: document.querySelector('#shelf [aria-current=true]')?.dataset.id ?? null,
    mark: !!document.querySelector('#frame .mark'),
    ready: document.getElementById('ready').textContent.replace(/\s+/g, ' ').trim(),
    focus: document.activeElement?.id || document.activeElement?.tagName,
    threads: document.querySelectorAll('#threads button[data-t]').length,
  }));
  async function clearBox() { await tap('#prompt'); await page.keyboard.press('Meta+A'); await page.keyboard.press('Backspace'); }
  async function make(words) {
    await clearBox(); await page.keyboard.type(words);
    const b = await count(); await tap('#go'); return landed(b);
  }

  await page.setViewportSize({width: 1440, height: 1000});
  await page.goto(BASE);
  await page.evaluate(() => localStorage.clear());
  await page.goto(BASE);
  await page.waitForTimeout(1200);

  // Setup: one earlier thread, so a new thread has something to be pulled back to.
  await make('An existing idea');
  await tap('#newThread');
  row((await screen()).title === 'A new thread', 'New thread opens an empty thread', await screen());

  // 1. A new image started from New thread is shown when it lands.
  await make('A green teapot on a windowsill');
  let s = await screen();
  row(s.title === 'A green teapot on a windowsill' && s.threads === 2, 'the image from New thread is shown when it lands', s);
  const teapot = +s.current;

  // 2. Words typed during a Try again stay about the image they were typed for.
  let b = await count();
  await tap('#again');
  await clearBox(); await page.keyboard.type('Make the wall green and keep the pot');
  await landed(b);
  s = await screen();
  row(s.chip === `About image ${teapot}` && s.go === `Change image ${teapot}`, 'typing during a render keeps the box on its image', s);
  row(s.prompt === 'Make the wall green and keep the pot', 'typed words survive the landing', s);
  row(s.current === String(teapot), 'the stage stays on the image being typed about', s);
  row(s.ready.includes(`Image ${teapot + 1} is ready`), 'the landed image is offered as ready', s);
  await tap('#showReady');
  s = await screen();
  row(s.current === String(teapot + 1) && s.ready === '', 'Show it opens the landed image and clears the offer', s);
  await clearBox();

  // 3. An area marked during a render stays on the image it was marked on.
  const cur = +(await screen()).current;
  b = await count();
  await tap('#again');
  await tap('#markBtn');
  const frameBox = async () => (await page.$('#frame'))?.boundingBox() ?? {x: 300, y: 200, width: 400, height: 400};
  let box = await frameBox();
  await page.mouse.move(box.x + box.width * .2, box.y + box.height * .2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * .6, box.y + box.height * .6, {steps: 6});
  await page.mouse.up();
  await landed(b);
  s = await screen();
  row(s.chip === `The marked area of image ${cur}` && s.mark && s.current === String(cur), 'an area marked during a render stays on its image', s);
  await page.keyboard.press('Escape');
  await page.mouse.click(5, 500);

  // 4. A drag that is still held when a render lands is not cut.
  const cur2 = +(await screen()).current;
  b = await count();
  await tap('#again');
  await tap('#markBtn');
  box = await frameBox();
  await page.mouse.move(box.x + box.width * .25, box.y + box.height * .25);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * .4, box.y + box.height * .4, {steps: 3});
  await until(async () => (await count()) >= b + 1);
  await page.waitForTimeout(1600);                       // the page's refresh runs while the button is held
  await page.mouse.move(box.x + box.width * .7, box.y + box.height * .7, {steps: 3});
  await page.mouse.up();
  s = await screen();
  // The area must run from where the drag started to where it ended (25% to 70%), not stop where the
  // landing cut it (40%), and the page must have left marking mode.
  const m = await page.evaluate(() => ({mark: view.mark && view.mark.map(v => +v.toFixed(2)), marking: view.marking}));
  row(s.chip === `The marked area of image ${cur2}` && m.mark && m.mark[2] > 0.4 && m.mark[3] > 0.4 && !m.marking,
      'a drag held across a landing is kept whole', {...s, ...m});
  await page.keyboard.press('Escape');

  // 5. A reader who went back to an earlier image is not pulled forward as more tries land.
  b = await count();
  await tap('#more');
  await tap('#again3');
  const first = await page.evaluate(() => document.querySelector('#shelf button')?.dataset.id ?? 'none');
  await tap(`#shelf button[data-id="${first}"]`);
  await landed(b, 3);
  s = await screen();
  row(s.current === first, 'the image the reader chose stays on the stage while tries land', s);

  // 6. A thread name being typed survives a landing, and typing carries on where it was.
  await until(idle);
  const stageBeforeRename = (await screen()).current;
  b = await count();
  await tap('#again');
  await tap('#rename');
  await page.keyboard.press('Meta+A');
  await page.keyboard.type('Teapot ideas');
  await landed(b);
  await page.keyboard.type(' v2');
  const t = await page.evaluate(() => ({value: document.getElementById('title')?.value, focus: document.activeElement?.id,
    stage: document.querySelector('#shelf [aria-current=true]')?.dataset.id}));
  row(t.value === 'Teapot ideas v2' && t.focus === 'title' && t.stage === stageBeforeRename, 'a rename in progress survives a landing, and the stage stays', {...t, stageBeforeRename});
  await page.keyboard.press('Enter');
  await page.waitForTimeout(1200);
  row((await screen()).title === 'Teapot ideas v2', 'the typed name is saved', await screen());

  // 7. A render landing in another thread is offered, not shown.
  await until(idle);
  const here = (await screen()).title;
  b = await count();
  await tap('#again');
  await tap('#threads button[data-t]:not([aria-current=true])');
  const other = (await screen()).title;
  await landed(b);
  s = await screen();
  row(s.title === other && s.title !== here && /is ready in/.test(s.ready), 'a render from another thread is offered, the open thread stays', s);

  // 8 to 10 need an image made from a source, so Compare and Check exist. Change the open image once.
  await until(idle);
  await tap('#dismissReady');
  await make('Make the light warmer');
  const src = (await screen()).current;
  const more = () => page.evaluate(() => !document.getElementById('morePop')?.hidden);

  // 8. A menu open on an image is not switched to the image that lands.
  b = await count();
  await tap('#again');
  await tap('#more');
  await landed(b);
  s = await screen();
  row(s.current === src && await more() && /is ready/.test(s.ready), 'the More menu stays on its image across a landing', {...s, src});
  await page.keyboard.press('Escape');

  // 9. A Check result stays beside the image it measured.
  await until(idle);
  b = await count();
  await tap('#again');
  await tap('#more'); await tap('#check');
  await page.waitForTimeout(600);
  await landed(b);
  s = await screen();
  const said = await page.evaluate(() => document.querySelector('#detail .say')?.textContent || '');
  row(s.current === src && /Measured/.test(said), 'a Check result stays with the image it measured', {...s, src, said});
  await tap('#showReady');

  // 10. Comparing an image with its source is not carried onto the image that lands.
  await until(idle);
  await tap(`#shelf button[data-id="${src}"]`);
  b = await count();
  await tap('#again');
  await tap('#compare');
  await landed(b);
  s = await screen();
  const cmp = await page.evaluate(() => ({comparing: view.comparing, tag: document.querySelector('#frame .tag')?.textContent || ''}));
  row(s.current === src && cmp.comparing && cmp.tag.includes(`image ${src}`), 'Compare stays on its image across a landing', {...s, ...cmp, src});

  return `ok=${out.filter(l => l.startsWith('ok')).length} fail=${out.filter(l => l.startsWith('FAIL')).length}\n` + out.join('\n');
}
