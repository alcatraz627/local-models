// Shared behaviour for the three studio directions: icons, theme, palette, and the fake view state.
// Each layout calls draw() after any change. Nothing here talks to the kit; these are looks to rule on.
const SPRITE = `<svg width="0" height="0" style="position:absolute" aria-hidden="true">
<symbol id="i-spark" viewBox="0 0 24 24"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 16v4M17 18h4"/></symbol>
<symbol id="i-image" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M3 16l5-5 4 4 3-3 6 6"/><circle cx="16" cy="9" r="1.5"/></symbol>
<symbol id="i-plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol>
<symbol id="i-x" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></symbol>
<symbol id="i-wand" viewBox="0 0 24 24"><path d="M5 19L16 8M14 6l4 4M18 3v3M16.5 4.5h3M6 5v2M5 6h2"/></symbol>
<symbol id="i-again" viewBox="0 0 24 24"><path d="M4 9a8 8 0 0 1 14.5-3M20 4v4h-4M20 15a8 8 0 0 1-14.5 3M4 20v-4h4"/></symbol>
<symbol id="i-pencil" viewBox="0 0 24 24"><path d="M4 20l4-1L19 8l-3-3L5 16z"/><path d="M14 7l3 3"/></symbol>
<symbol id="i-star" viewBox="0 0 24 24"><path d="M12 4l2.5 5.2 5.7.8-4.1 4 1 5.6L12 17l-5.1 2.6 1-5.6-4.1-4 5.7-.8z"/></symbol>
<symbol id="i-down" viewBox="0 0 24 24"><path d="M12 4v11M7 11l5 5 5-5M5 20h14"/></symbol>
<symbol id="i-theme" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 0 0 16z" fill="currentColor"/></symbol>
<symbol id="i-help" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.6 2.2c-.7.4-1.1 1-1.1 1.8M12 17h.01"/></symbol>
<symbol id="i-chev" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></symbol>
<symbol id="i-lock" viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></symbol>
<symbol id="i-area" viewBox="0 0 24 24"><path d="M4 8V5h3M17 5h3v3M20 16v3h-3M7 19H4v-3"/><rect x="8" y="9" width="8" height="6" rx="1"/></symbol>
<symbol id="i-split" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M12 3v18"/></symbol>
<symbol id="i-more" viewBox="0 0 24 24"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></symbol>
<symbol id="i-attach" viewBox="0 0 24 24"><path d="M20 11l-8.5 8.5a5 5 0 0 1-7-7L13 4a3.3 3.3 0 0 1 4.7 4.7L9.2 17.2a1.7 1.7 0 0 1-2.4-2.4L14.5 7"/></symbol>
<symbol id="i-sliders" viewBox="0 0 24 24"><path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/></symbol>
<symbol id="i-expand" viewBox="0 0 24 24"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></symbol>
<symbol id="i-logo" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="5"/><path d="M6.5 16.5l3.5-4.5 3 3.5 2-2.5 2.5 3.5" /><circle cx="15.5" cy="8.5" r="1.4"/></symbol>
</svg>`;
document.body.insertAdjacentHTML('afterbegin', SPRITE);
const icon = n => `<svg class="i"><use href="#i-${n}"/></svg>`;
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const $ = id => document.getElementById(id);

const params = new URLSearchParams(location.search);
document.documentElement.dataset.palette = ['blue', 'amber'].includes(params.get('palette')) ? params.get('palette') : 'graphite';
if (['light', 'dark'].includes(params.get('theme'))) document.documentElement.dataset.theme = params.get('theme');
function toggleTheme() {
  const now = document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  document.documentElement.dataset.theme = now === 'dark' ? 'light' : 'dark';
}

// Threads, newest first, each with its images oldest first, and a short title from the first prompt.
const THREADS = [...new Set(RECORDS.map(r => r.thread))].reverse().map(t => {
  const imgs = RECORDS.filter(r => r.thread === t);
  const titles = {bicycle: 'Red bicycle, wet brick wall', harbour: 'Harbour at sunrise', teapot: 'Green teapot on a windowsill'};
  const key = Object.keys(titles).find(k => imgs[0].prompt.toLowerCase().includes(k));
  return {id: t, title: titles[key] || imgs[0].prompt, imgs};
});
const view = {thread: THREADS[0].id, selected: null, mode: 'change'};
const thread = () => THREADS.find(t => t.id === view.thread);
const current = () => { const t = thread(); return t.imgs.find(i => i.id === view.selected) || t.imgs[t.imgs.length - 1]; };
const how = r => r.mode === 'new' ? 'From words alone' : r.parent ? `A change to image ${r.parent}` : 'Reworked';
function pick(id) { view.selected = id; draw(); }
function openThread(id) { view.thread = id; view.selected = null; draw(); }
function setMode(m) { view.mode = m; draw(); }
// The writing box, the same in every layout. Its two modes are always on screen, so starting a new
// image is one press and never hidden behind a chip.
function composer() {
  const c = current(), change = view.mode === 'change';
  return `<div class="mode" role="group" aria-label="What your words do">
      <button type="button" aria-pressed="${change}" onclick="setMode('change')">${icon('pencil')}Change image ${c.id}</button>
      <button type="button" aria-pressed="${!change}" onclick="setMode('new')">${icon('plus')}New image</button></div>
    <textarea rows="2" aria-label="${change ? 'What should change' : 'What you want to see'}" placeholder="${change
      ? 'What should change? Warmer light, remove the sign, make it night' : 'A red bicycle leaning on a wet brick wall, early morning'}"></textarea>
    <div class="tools">
      <button type="button" class="icon" data-tip="Add an image to rework or combine">${icon('attach')}</button>
      <button type="button" class="icon" data-tip="Improve my words">${icon('wand')}</button>
      ${change ? '' : `<button type="button" class="icon" data-tip="Style, tries, size, steps and seed">${icon('sliders')}</button>`}
      <span class="where">${icon('lock')}Drawn on this computer</span>
      <span style="flex:1"></span>
      <button type="button" class="go">${change ? icon('pencil') + 'Change' : icon('spark') + 'Make image'}</button>
    </div>`;
}
if (params.get('mode') === 'new') view.mode = 'new';
if (params.get('thread')) { const t = THREADS[+params.get('thread')]; if (t) view.thread = t.id; }
