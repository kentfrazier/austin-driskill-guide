(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const cards = $$('.place-card');
  const sections = $$('.filterable-section');
  const search = $('#guide-search');
  const walk = $('#walk-only');
  const savedDialog = $('#saved-dialog');
  const STORE = 'austin-driskill-guide-2026-picks';
  const THEME = 'austin-driskill-guide-theme';
  const festivalPanel = $('.festival-panel');
  const festivalRows = $$('.festival-row');
  let festivalWasOpen = false;
  let previousQuery = '';
  const knownIds = new Set(cards.map(c => c.id));
  let saved = new Set();
  let toastTimer;
  try {
    const stored = JSON.parse(localStorage.getItem(STORE) || '[]');
    if (Array.isArray(stored)) saved = new Set(stored.filter(id => knownIds.has(id)));
  } catch (_) {}
  const state = Object.fromEntries(sections.map(s => [s.id, { category: 'all', expanded: false }]));
  function notify(text) {
    const toast = $('#toast');
    clearTimeout(toastTimer);
    toast.textContent = text;
    toast.hidden = false;
    toastTimer = setTimeout(() => { toast.hidden = true; }, 2400);
  }
  function syncSaved() {
    $$('[data-save]').forEach(button => {
      const id = button.dataset.save;
      const isSaved = saved.has(id);
      const name = document.getElementById(id)?.dataset.name || 'place';
      button.setAttribute('aria-pressed', String(isSaved));
      button.setAttribute('aria-label', `${isSaved ? 'Remove' : 'Save'} ${name}${isSaved ? ' from your picks' : ' to your picks'}`);
    });
    $('#saved-count').textContent = saved.size;
    $('#open-saved').setAttribute('aria-label', `View your ${saved.size} saved picks`);
    renderSaved();
  }
  function save(id) {
    if (!knownIds.has(id)) return;
    if (saved.has(id)) { saved.delete(id); notify('Removed from your picks'); }
    else { saved.add(id); notify('Added to your picks'); }
    try { localStorage.setItem(STORE, JSON.stringify([...saved])); } catch (_) {}
    syncSaved();
  }
  function renderSaved() {
    const list = $('#saved-items');
    list.replaceChildren();
    $('#saved-empty').hidden = saved.size > 0;
    [...saved].forEach(id => {
      const card = document.getElementById(id);
      if (!card) return;
      const item = document.createElement('div');
      item.className = 'saved-item';
      const link = document.createElement('a');
      link.href = `#${id}`;
      const title = document.createElement('strong');
      title.textContent = card.dataset.name;
      const info = document.createElement('small');
      info.textContent = `${card.dataset.category} · ${card.dataset.travel}`;
      link.append(title, info);
      link.addEventListener('click', () => { savedDialog.close(); reveal(id); });
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'icon-button';
      remove.setAttribute('aria-label', `Remove ${card.dataset.name} from your picks`);
      remove.innerHTML = '<svg aria-hidden="true"><use href="#i-close"></use></svg>';
      remove.addEventListener('click', () => { save(id); if (!saved.size) $('#close-saved').focus(); });
      item.append(link, remove);
      list.append(item);
    });
  }
  function applyFilters() {
    const query = search.value.trim().toLocaleLowerCase();
    let total = 0;
    $('#clear-search').hidden = !query;
    sections.forEach(section => {
      const config = state[section.id];
      const allCards = $$('.place-card', section);
      const matched = allCards.filter(card => {
        const matchCategory = config.category === 'all' || card.dataset.category === config.category || card.dataset.tags.split('|').includes(config.category);
        const matchQuery = !query || query.split(/\s+/).every(term => card.dataset.search.includes(term));
        return matchCategory && matchQuery && (!walk.checked || card.dataset.mode === 'walk');
      });
      const allMatches = new Set(matched);
      const shouldLimit = !query && !walk.checked && config.category === 'all' && !config.expanded;
      const limit = Number(section.dataset.limit || 6);
      allCards.forEach(card => { card.hidden = !allMatches.has(card) || (shouldLimit && matched.indexOf(card) >= limit); });
      total += matched.length;
      $('.empty-state', section).hidden = matched.length > 0;
      const more = $('.show-more', section);
      more.parentElement.hidden = !!query || walk.checked || config.category !== 'all' || matched.length <= limit;
      more.textContent = config.expanded ? 'Show fewer choices' : `See all ${matched.length} choices`;
      more.setAttribute('aria-expanded', String(config.expanded));
      $('.section-count', section).textContent = `${matched.length} ${matched.length === 1 ? 'choice' : 'choices'}${shouldLimit && matched.length > limit ? ` · showing ${limit}` : ''}`;
    });
    const festivalAllowed = ['all', 'Improv'].includes(state.entertainment.category);
    const festivalMatches = festivalRows.filter(row => festivalAllowed && (!walk.checked || row.dataset.mode === 'walk') && (!query || query.split(/\s+/).every(term => row.dataset.search.includes(term))));
    festivalRows.forEach(row => { row.hidden = !festivalMatches.includes(row); });
    $$('.festival-group').forEach(group => { group.hidden = !$('.festival-row:not([hidden])', group); });
    festivalPanel.hidden = !festivalAllowed || !festivalMatches.length;
    $('#festival-label').textContent = query || walk.checked ? `${festivalMatches.length} matching festival blocks` : 'The full Saturday lineup';
    if (query && !previousQuery) festivalWasOpen = festivalPanel.open;
    if (query && festivalMatches.length) festivalPanel.open = true;
    if (!query && previousQuery) festivalPanel.open = festivalWasOpen;
    previousQuery = query;
    if ((query || walk.checked) && festivalMatches.length) $('#entertainment .empty-state').hidden = true;
    $('#search-status').textContent = query || walk.checked ? `${total} matching ${total === 1 ? 'card' : 'cards'}${festivalMatches.length ? ` · ${festivalMatches.length} festival ${festivalMatches.length === 1 ? 'block' : 'blocks'}` : ''}${walk.checked ? ' · walkable' : ''}${query ? ` for “${search.value.trim()}”` : ''}` : '';
    $('#quick-picks').hidden = !!query || walk.checked;
  }
  function reveal(id) {
    const card = document.getElementById(id);
    if (!card?.classList.contains('place-card')) return;
    const section = card.closest('.filterable-section');
    search.value = '';
    walk.checked = false;
    state[section.id] = { category: 'all', expanded: true };
    $$('.chip', section).forEach(b => b.setAttribute('aria-pressed', String(b.dataset.filter === 'all')));
    applyFilters();
    $('details', card).open = true;
    requestAnimationFrame(() => card.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }));
  }
  $$('[data-save]').forEach(button => button.addEventListener('click', () => save(button.dataset.save)));
  search.addEventListener('input', applyFilters);
  walk.addEventListener('change', applyFilters);
  $('#clear-search').addEventListener('click', () => { search.value = ''; search.focus(); applyFilters(); });
  sections.forEach(section => {
    $$('.chip', section).forEach(button => button.addEventListener('click', () => {
      state[section.id].category = button.dataset.filter;
      $$('.chip', section).forEach(b => b.setAttribute('aria-pressed', String(b === button)));
      applyFilters();
    }));
    $('.show-more', section).addEventListener('click', () => {
      const previous = state[section.id].expanded;
      state[section.id].expanded = !previous;
      applyFilters();
      if (previous) section.scrollIntoView({ block: 'start', behavior: 'smooth' });
    });
  });
  $('#open-saved').addEventListener('click', () => { renderSaved(); savedDialog.showModal(); });
  $('#close-saved').addEventListener('click', () => savedDialog.close());
  savedDialog.addEventListener('click', event => { if (event.target === savedDialog) { const r = savedDialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) savedDialog.close(); } });
  const mapPreference = $('#map-preference');
  const mapPreferenceKey = 'austin-driskill-guide-map-preference';
  try {
    const preferredMap = localStorage.getItem(mapPreferenceKey);
    if (preferredMap === 'apple' || preferredMap === 'google') mapPreference.value = preferredMap;
  } catch (_) {}
  document.documentElement.dataset.mapPreference = mapPreference.value;
  mapPreference.addEventListener('change', () => {
    document.documentElement.dataset.mapPreference = mapPreference.value;
    try { localStorage.setItem(mapPreferenceKey, mapPreference.value); } catch (_) {}
  });
  $('#theme-toggle').addEventListener('click', () => {
    const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem(THEME, theme); } catch (_) {}
    $('#theme-toggle').setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
    $('#theme-toggle').setAttribute('aria-pressed', String(theme === 'dark'));
  });
  $('#theme-toggle').setAttribute('aria-label', `Switch to ${document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'} mode`);
  $('#theme-toggle').setAttribute('aria-pressed', String(document.documentElement.dataset.theme === 'dark'));
  $$('a[data-reveal]').forEach(a => a.addEventListener('click', () => reveal(a.getAttribute('href').slice(1))));
  window.addEventListener('hashchange', () => { const id = decodeURIComponent(location.hash.slice(1)); if (knownIds.has(id)) reveal(id); });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.filter(e => e.isIntersecting).forEach(e => {
        $$('.nav-inner a').forEach(a => { const active = a.getAttribute('href') === `#${e.target.id}`; a.classList.toggle('active', active); if (active) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current'); });
      });
    }, { rootMargin: '-15% 0px -65% 0px', threshold: 0 });
    $$('.guide-section').forEach(s => observer.observe(s));
  }
  $('#print-guide').addEventListener('click', () => {
    const details = $$('details');
    const openBefore = details.map(d => d.open);
    details.forEach(d => { d.open = true; });
    window.addEventListener('afterprint', () => { details.forEach((d, i) => { d.open = openBefore[i]; }); }, { once: true });
    window.print();
  });
  const austinDate = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Chicago', year:'numeric',month:'2-digit',day:'2-digit' }).format(new Date());
  if (austinDate > '2026-11-07') $('#archive-note').hidden = false;
  syncSaved();
  applyFilters();
  const firstId = decodeURIComponent(location.hash.slice(1));
  if (knownIds.has(firstId)) reveal(firstId);
})();
