// Uses the studio the way a person would, inside the page, and reports one line per step.
//
// Start a kit server with the stand-in engine, an empty data folder and no key for GPT:
//   env IMAGINE_KIT_FAKE=1 IMAGINE_KIT_FAKE_STEP_S=1 IMAGINE_KIT_FAKE_MISSING=gpt IMAGINE_KIT_DATA=<empty folder> \
//       python3 kit.py app --port 6281 --no-open
// Then, from a browser driver: open the page, add this file as a script, and call window.__walk(1),
// reload, add it again and call window.__walk(2). window.__measure() reports fit at the current width.
// Not covered here: a failed render (tests/ui_check.sh photographs it) and choosing a file from disk.
(() => {
  const $ = s => document.querySelector(s), wait = ms => new Promise(r => setTimeout(r, ms));
  const state = async () => (await fetch('/api/state')).json();
  const text = s => ($(s) || {}).textContent?.trim() ?? null;
  const press = s => { const e = $(s); if (!e) throw new Error('nothing to press: ' + s); e.focus(); e.click(); };
  const type = (s, v) => { const e = $(s); e.focus(); e.value = v; e.dispatchEvent(new Event('input', {bubbles: true})); };
  const pick = (s, v) => { const e = $(s); e.value = v; e.dispatchEvent(new Event('change', {bubbles: true})); };
  const more = async id => { if (!$('#' + id) || !$('#' + id).offsetParent) press('#more'); await wait(50); press('#' + id); };
  // Wait until the history holds `want` images and nothing is still being drawn.
  const until = async want => { for (let i = 0; i < 150; i++) { const s = await state();
    if (s.history.length >= want && !s.jobs.some(j => j.state === 'queued' || j.state === 'running') && !$('.job')) { await wait(1300); return s; } await wait(400); }
    throw new Error('timed out waiting for ' + want + ' images'); };
  const send = async () => { const have = (await state()).history.length; press('#go'); return until(have + 1); };
  const drag = async (x1, y1, x2, y2) => { const f = $('#frame'); await f.querySelector('img').decode(); const r = f.getBoundingClientRect();
    const fire = (t, x, y) => f.dispatchEvent(new PointerEvent(t, {bubbles: true, pointerId: 1, clientX: r.left + r.width * x, clientY: r.top + r.height * y}));
    fire('pointerdown', x1, y1); fire('pointermove', (x1 + x2) / 2, (y1 + y2) / 2); fire('pointermove', x2, y2); fire('pointerup', x2, y2); };
  const key = (k, o = {}) => document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: k, bubbles: true, ...o}));

  window.__measure = () => {
    const cut = [...document.querySelectorAll('button, select, a.btn, h1, h2, summary')].filter(e => e.offsetParent && e.scrollWidth > e.clientWidth + 1).map(e => e.id || e.textContent.trim().slice(0, 20));
    const over = document.documentElement.scrollWidth - innerWidth, dots = /\.\.\.|…/.test(document.body.innerText);
    return (over <= 1 && !cut.length && !dots ? 'ok   ' : 'FAIL ') + `at ${innerWidth} wide with ${document.documentElement.dataset.size} text: no sideways scroll, every control's words fit, no ellipsis` + (over > 1 || cut.length || dots ? '  (got: ' + JSON.stringify({over, cut, dots}) + ')' : '');
  };

  window.__walk = async phase => {
    const out = [], ok = (name, cond, got) => out.push((cond ? 'ok   ' : 'FAIL ') + name + (cond || got === undefined ? '' : '  (got: ' + JSON.stringify(got) + ')'));
    try {
      if (phase === 1) {
        ok('an empty studio says the box starts a new thread', text('#newSay') === 'The first image of a new thread' && text('#go') === 'Make image', text('#go'));
        type('#prompt', 'A lighthouse on a rocky coast at dusk'); pick('#tries', '2');
        const style = $('#style').options[1].value; pick('#style', style);
        ok('the button says how many images it will make', text('#go') === 'Make 2 images', text('#go'));
        press('#go'); for (let i = 0; i < 20 && document.querySelectorAll('.job').length < 2; i++) await wait(200);
        ok('two tries wait in line', document.querySelectorAll('.job').length === 2);
        const stops = () => [...document.querySelectorAll('.job .stop')]; stops().pop().focus(); stops().pop().click(); await wait(100);
        ok('one press on stop cancels nothing and asks again', (await state()).jobs.filter(j => j.state === 'queued' || j.state === 'running').length === 2 && stops().pop().textContent.trim() === 'Confirm stop', stops().pop().textContent);
        ok('the stop button keeps keyboard focus while the page refreshes', document.activeElement === stops().pop());
        type('#prompt', 'half typed words'); await wait(1500);
        ok('typing while an image is drawn keeps every letter and the cursor', $('#prompt').value === 'half typed words' && document.activeElement === $('#prompt'), $('#prompt').value);
        type('#prompt', '');
        let s = await until(2);
        ok('a new thread holds the two tries', s.history.length === 2 && s.history[0].thread === s.history[1].thread, s.history.length);
        ok('the chosen style is recorded on both images', s.history.every(h => h.style === style), s.history.map(h => h.style));
        const first = +$('#shelf [aria-current=true]').dataset.id;
        ok('the box is now about the image on screen', text('#subjectSay') === `About image ${first}` && text('#go') === `Change image ${first}`, [text('#subjectSay'), text('#go')]);

        type('#prompt', 'Make it night, with the lamp lit'); s = await send(); let n = s.history[0];
        ok('a change made one new image from the open one', n.mode === 'edit' && n.parent === first && s.history.length === 3, [n.mode, n.parent]);
        ok('the new image is the one on screen', $('#shelf [aria-current=true]').dataset.id === String(n.id));
        ok('the box is empty after sending', $('#prompt').value === '');

        press('#star'); await wait(700);
        ok('star marks the image', (await state()).history[0].star === true);
        ok('pressing a button leaves keyboard focus on it', document.activeElement.id === 'star', document.activeElement.id || document.activeElement.tagName);
        $('#how').open = true; $('#how').dispatchEvent(new Event('toggle')); press('#star'); await wait(700);
        ok('an opened section stays open after another press', $('#how').open === true);
        press('#compare');
        ok('compare shows the image it was made from, not the new one', $('#frame img').getAttribute('src') === n.source_urls[0] && n.source_urls[0] !== n.url && !!$('#frame .tag'));
        press('#compare');
        await more('check'); for (let i = 0; i < 20 && !$('.say'); i++) await wait(200);
        ok('check says how much changed', /Measured/.test(text('.say') || ''), text('.say'));
        const count = (await state()).history.length;
        await more('del'); await wait(100);
        ok('one press on delete removes nothing and asks again', (await state()).history.length === count && text('#del') === 'Confirm delete', text('#del'));
        press('#del'); await wait(1200);
        ok('a second press removes the image', (await state()).history.length === count - 1);

        const under = +$('#shelf [aria-current=true]').dataset.id;
        press('#markBtn'); await drag(.2, .2, .6, .5);
        ok('dragging on the image marks that area', text('#subjectSay') === `The marked area of image ${under}` && text('#go') === 'Change the area', [text('#subjectSay'), text('#go')]);
        type('#prompt', 'Add a sailing boat'); s = await send(); n = s.history[0];
        ok('the area change is recorded with its area, from the image that was open', !!n.region && n.parent === under, [n.region, n.parent]);

        press('#detail button[data-src="0"]'); press('#markBtn'); await drag(.1, .1, .5, .4);
        ok('marking a source is about that source, not the open image', text('#subjectSay') === `The marked area of a source of image ${n.id}`, text('#subjectSay'));
        type('#prompt', 'Brighten this corner'); s = await send(); const n2 = s.history[0];
        ok('the change to a source starts from that source and joins the thread', n2.sources[0] === n.sources[0] && !!n2.region && n2.thread === n.thread, [n2.sources, n2.thread]);

        // Try again repeats a request with the model that made the image, so the picker is tested on a new image.
        pick('#model', 'gpt'); const had = (await state()).history.length; press('#subjectClear'); type('#prompt', 'A harbour at sunrise'); press('#go');
        for (let i = 0; i < 20 && !$('#fail .notice'); i++) await wait(200);
        ok('a new image is refused while the model has no key, and the page says why', (await state()).history.length === had && (text('#fail strong') || '').length > 0, text('#fail strong'));
        ok('the words stay in the box after a refusal', $('#prompt').value === 'A harbour at sunrise');
        type('#prompt', ''); type('#keyBox', 'abcd'); await wait(2500);
        ok('a half-typed key is still there after the page refreshes itself', ($('#keyBox') || {}).value === 'abcd', ($('#keyBox') || {}).value);
        pick('#model', (await state()).default_model); press('#failClose');

        press('#more'); await wait(50);
        ok('the More menu opens on a press and stays open', !!$('#morePop') && !$('#morePop').hidden);
        press('#reuse');
        ok('use as source puts the image in the box and renames the button', document.querySelectorAll('#thumbs .thumb').length === 1 && text('#go') === 'Rework this', text('#go'));
        type('#prompt', 'kept words');
      }
      if (phase === 2) {
        for (let i = 0; i < 20 && !$('#thumbs .thumb'); i++) await wait(200);
        ok('the draft survives a reload with its source image intact', $('#prompt').value === 'kept words' && !!$('#thumbs img') && (await $('#thumbs img').decode().then(() => true, () => false)));
        press('#thumbs .thumb button'); type('#prompt', '');
        press('#addPhoto'); const open = !$('#photoPop').hidden; $('#stage').click();
        ok('a click outside an open panel closes it', open && $('#photoPop').hidden);
        press('#newThread'); press('#settings');
        for (const [id, v] of [['#width', '512'], ['#height', '512'], ['#steps', '6'], ['#seed', '1234']]) type(id, v);
        key('Escape');
        ok('escape closes the settings panel', $('#settingsPop').hidden);
        const have = (await state()).history.length;
        type('#prompt', 'A cabin in winter snow'); pick('#tries', '1'); key('Enter', {metaKey: true});
        const n = (await until(have + 1)).history[0];
        ok('command with enter sends the box, and size, steps and seed reach the image', n.width === 512 && n.height === 512 && n.steps === 6 && n.seed === 1234, [n.width, n.height, n.steps, n.seed]);
        ok('an image started from New thread is the one on screen when it lands', ($('#shelf [aria-current=true]') || {dataset: {}}).dataset.id === String(n.id) && document.querySelectorAll('#shelf button').length === 1, ($('#shelf [aria-current=true]') || {dataset: {}}).dataset.id);
        ok('size, steps and seed are cleared once they have been used', ['#width', '#height', '#steps', '#seed'].every(id => $(id).value === ''));
        press('#again'); type('#prompt', 'keep me'); const s2 = await until(have + 2);
        ok('a render that lands while words are in the box does not change what the box is about', $('#prompt').value === 'keep me' && text('#subjectSay') === `About image ${n.id}` && $('#shelf [aria-current=true]').dataset.id === String(n.id), [text('#subjectSay'), $('#prompt').value]);
        ok('the image that landed is in the strip all the same', document.querySelectorAll('#shelf button').length === 2 && s2.history.length === have + 2);
        type('#prompt', '');
        const theme = document.documentElement.dataset.theme; press('#theme');
        ok('the theme button switches light and dark', document.documentElement.dataset.theme !== theme);
      }
    } catch (e) { out.push('FAIL the walk stopped: ' + e.message); }
    return out.join('\n');
  };
})();
