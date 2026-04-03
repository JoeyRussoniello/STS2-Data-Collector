import { fmt, pct, wrColor } from '../utils.js';

let sortCol = 'win_rate_when_present';
let sortAsc = false;

function sortData(data) {
  return [...data].sort((a, b) => {
    let va = a[sortCol], vb = b[sortCol];
    if (va == null) va = -Infinity;
    if (vb == null) vb = -Infinity;
    return sortAsc ? va - vb : vb - va;
  });
}

const PAGE_SIZE = 20;
let currentPage = 0;
let allCards = [];

export async function renderCards(el, api, steamId = null) {
  el.innerHTML = '<div class="loading-state"><div class="eldritch-spinner"></div><p>Indexing the catalog of power…</p></div>';
  sortCol = 'win_rate_when_present';
  sortAsc = false;
  currentPage = 0;

  try {
    allCards = await api.getCards({ min_appearances: 3, steam_id: steamId });

    el.innerHTML = `
      <div class="page-header">
        <h1>${steamId ? 'Personal Card Analytics' : 'Card Analytics Deep-Dive'}</h1>
        <p class="page-header__desc">${steamId
          ? 'Card performance data scoped to this player\u2019s recorded runs.'
          : 'An exhaustive examination of the ethereal constructs that shape your destiny. Data harvested from the deep spires, tracking performance across every timeline.'}</p>
      </div>

      <div class="filter-bar" id="card-filters">
        <div class="filter-group">
          <label class="filter-label">Character</label>
          <select class="filter-select" id="card-char">
            <option value="">All Characters</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Ascension</label>
          <select class="filter-select" id="card-asc">
            <option value="">All Levels</option>
            ${Array.from({length: 21}, (_, i) => `<option value="${i}">Ascension ${i}</option>`).join('')}
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Min Appearances</label>
          <input type="number" class="filter-input" id="card-min" value="3" min="1" style="width:100px">
        </div>
        <button class="filter-btn" id="card-apply">Apply Filters</button>
        <div style="flex:1"></div>
        <div style="align-self:center;font-size:.8rem;color:var(--on-surface-dim)">
          <span id="card-count">${allCards.length}</span> unique cards
        </div>
      </div>

      <div class="panel mb-0">
        <h3 class="panel__subtitle">The Catalog of Power</h3>
        <div id="card-table-wrap"></div>
        <div id="card-pagination" class="pagination"></div>
      </div>
    `;

    // Populate character dropdown from the data
    const charSet = new Set();
    allCards.forEach(c => {
      const parts = c.card_id.split('_');
      // We don't have character info per card from this endpoint
    });

    // Try to populate characters from a separate call
    try {
      const chars = await api.getCharacters();
      const sel = document.getElementById('card-char');
      chars.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.character;
        opt.textContent = fmt(c.character);
        sel.appendChild(opt);
      });
    } catch (_) { /* non-critical */ }

    renderCardTable();

    document.getElementById('card-apply').addEventListener('click', async () => {
      const wrap = document.getElementById('card-table-wrap');
      wrap.innerHTML = '<div class="loading-state"><div class="eldritch-spinner"></div></div>';
      currentPage = 0;
      try {
        allCards = await api.getCards({
          steam_id: steamId,
          character: document.getElementById('card-char').value || undefined,
          ascension: document.getElementById('card-asc').value || undefined,
          min_appearances: document.getElementById('card-min').value || 3,
        });
        document.getElementById('card-count').textContent = allCards.length;
        renderCardTable();
      } catch (e) {
        wrap.innerHTML = `<div class="error-state"><p>${e.message}</p></div>`;
      }
    });
  } catch (err) {
    el.innerHTML = `<div class="error-state">
      <h2>Connection to the Archive Failed</h2>
      <p>${err.message}</p>
      <p class="text-dim">Check your API configuration in Settings (⚙).</p>
    </div>`;
  }
}

function renderCardTable() {
  const wrap = document.getElementById('card-table-wrap');
  const pag = document.getElementById('card-pagination');
  const sorted = sortData(allCards);
  const total = sorted.length;
  const pages = Math.ceil(total / PAGE_SIZE);
  const slice = sorted.slice(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE);

  const maxWR = Math.max(...allCards.map(c => c.win_rate_when_present), 0.01);

  const cols = [
    { key: 'card_id', label: 'Name', cls: '' },
    { key: 'win_rate_when_present', label: 'Win Rate When Drafted', cls: 'cell-bar' },
    { key: 'times_in_deck', label: 'Times In Deck', cls: 'cell-num' },
    { key: 'avg_copies_per_deck', label: 'Avg Copies', cls: 'cell-num' },
    { key: 'avg_floor_added', label: 'Avg Floor Added', cls: 'cell-num' },
    { key: 'avg_upgrade_level', label: 'Avg Upgrade', cls: 'cell-num' },
  ];

  wrap.innerHTML = `
    <table class="data-table">
      <thead><tr>
        ${cols.map(c => `<th class="${c.cls} ${sortCol === c.key ? 'sort-active' + (sortAsc ? ' sort-asc' : '') : ''}" data-col="${c.key}">${c.label}</th>`).join('')}
      </tr></thead>
      <tbody>
        ${slice.map(card => `<tr>
          <td class="cell-name">${fmt(card.card_id)}</td>
          <td class="cell-bar">
            <div class="wr-cell">
              <div class="wr-bar"><div class="wr-bar__fill" style="width:${(card.win_rate_when_present / maxWR) * 100}%;background:${wrColor(card.win_rate_when_present)}"></div></div>
              <span class="wr-val" style="color:${wrColor(card.win_rate_when_present)}">${pct(card.win_rate_when_present)}</span>
            </div>
          </td>
          <td class="cell-num">${card.times_in_deck.toLocaleString()}</td>
          <td class="cell-num">${card.avg_copies_per_deck.toFixed(1)}</td>
          <td class="cell-num">${card.avg_floor_added.toFixed(1)}</td>
          <td class="cell-num">${card.avg_upgrade_level != null ? card.avg_upgrade_level.toFixed(1) : '—'}</td>
        </tr>`).join('')}
      </tbody>
    </table>
  `;

  // Sortable headers
  wrap.querySelectorAll('th[data-col]').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      if (sortCol === col) { sortAsc = !sortAsc; } else { sortCol = col; sortAsc = false; }
      renderCardTable();
    });
  });

  // Pagination
  const start = currentPage * PAGE_SIZE + 1;
  const end = Math.min((currentPage + 1) * PAGE_SIZE, total);
  pag.innerHTML = `
    <span class="pagination__info">Displaying ${start}–${end} of ${total} Records</span>
    <div class="pagination__btns">
      ${currentPage > 0 ? '<button class="page-btn" data-p="prev">← Previous Leaf</button>' : ''}
      ${Array.from({length: Math.min(pages, 5)}, (_, i) => {
        const p = currentPage < 3 ? i : currentPage - 2 + i;
        if (p >= pages) return '';
        return `<button class="page-btn ${p === currentPage ? 'active' : ''}" data-p="${p}">${p + 1}</button>`;
      }).join('')}
      ${currentPage < pages - 1 ? '<button class="page-btn" data-p="next">Next Leaf →</button>' : ''}
    </div>
  `;

  pag.querySelectorAll('.page-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const v = btn.dataset.p;
      if (v === 'prev') currentPage--;
      else if (v === 'next') currentPage++;
      else currentPage = parseInt(v);
      renderCardTable();
      document.getElementById('card-table-wrap').scrollIntoView({ behavior: 'smooth' });
    });
  });
}
