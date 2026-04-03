function fmt(id) {
  return id.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/\b\w/g, c => c.toUpperCase());
}
function pct(v) { return (v * 100).toFixed(1) + '%'; }
function fmtTime(s) {
  if (!s) return '—';
  const m = Math.floor(s / 60), sec = Math.floor(s % 60);
  return m > 60 ? `${Math.floor(m / 60)}h ${m % 60}m` : `${m}:${String(sec).padStart(2, '0')}`;
}
function wrColor(rate) {
  if (rate >= 0.55) return 'var(--secondary)';
  if (rate >= 0.40) return 'var(--primary)';
  return 'var(--tertiary-dim)';
}

export async function renderCharacters(el, api, steamId = null) {
  el.innerHTML = '<div class="loading-state"><div class="eldritch-spinner"></div><p>Summoning character records…</p></div>';

  try {
    const chars = await api.getCharacters({ steam_id: steamId });

    if (!chars.length) {
      el.innerHTML = '<div class="empty-state"><p>The archive holds no character records yet.</p></div>';
      return;
    }

    el.innerHTML = `
      <div class="page-header">
        <h1>${steamId ? 'Personal Character Stats' : 'Character Performance'}</h1>
        <p class="page-header__desc">${steamId
          ? 'Per-character breakdowns for this player\u2019s recorded runs.'
          : 'Per-character breakdowns: win rates, run durations, deck composition, and relic usage across all recorded ascents.'}</p>
      </div>
      <div class="filter-bar" id="char-filters">
        <div class="filter-group">
          <label class="filter-label">Ascension</label>
          <select class="filter-select" id="char-asc">
            <option value="">All Levels</option>
            ${Array.from({length: 21}, (_, i) => `<option value="${i}">Ascension ${i}</option>`).join('')}
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Game Mode</label>
          <select class="filter-select" id="char-mode">
            <option value="">All Modes</option>
            <option value="Standard">Standard</option>
            <option value="Sealed">Sealed</option>
            <option value="Bespoke">Bespoke</option>
          </select>
        </div>
        <button class="filter-btn" id="char-apply">Apply Filters</button>
      </div>
      <div id="char-grid" class="char-grid"></div>
    `;

    renderCharGrid(chars);

    document.getElementById('char-apply').addEventListener('click', async () => {
      const asc = document.getElementById('char-asc').value;
      const mode = document.getElementById('char-mode').value;
      const grid = document.getElementById('char-grid');
      grid.innerHTML = '<div class="loading-state"><div class="eldritch-spinner"></div></div>';
      try {
        const filtered = await api.getCharacters({
          steam_id: steamId,
          ascension: asc || undefined,
          game_mode: mode || undefined,
        });
        renderCharGrid(filtered);
      } catch (e) {
        grid.innerHTML = `<div class="error-state"><p>${e.message}</p></div>`;
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

function renderCharGrid(chars) {
  const grid = document.getElementById('char-grid');
  if (!chars.length) {
    grid.innerHTML = '<div class="empty-state"><p>No character data matches the current filters.</p></div>';
    return;
  }

  grid.innerHTML = chars.map(c => `
    <div class="char-card">
      <div class="char-card__name">${fmt(c.character)}</div>
      <div class="char-card__runs">${c.run_count.toLocaleString()} runs · ${c.win_count.toLocaleString()} wins</div>
      <div class="char-card__wr" style="color:${wrColor(c.win_rate)}">${pct(c.win_rate)}</div>
      <div class="char-card__wr-label">Win Rate</div>
      <div class="char-card__bar">
        <div class="char-card__bar-fill" style="width:${c.win_rate * 100}%;background:${wrColor(c.win_rate)}"></div>
      </div>
      <div class="char-card__stats">
        <div>
          <span class="char-card__stat-val">${fmtTime(c.avg_run_time_seconds)}</span>
          <span class="char-card__stat-lbl">Avg Time</span>
        </div>
        <div>
          <span class="char-card__stat-val">${c.avg_deck_size.toFixed(1)}</span>
          <span class="char-card__stat-lbl">Avg Deck</span>
        </div>
        <div>
          <span class="char-card__stat-val">${c.avg_relic_count.toFixed(1)}</span>
          <span class="char-card__stat-lbl">Avg Relics</span>
        </div>
      </div>
    </div>
  `).join('');
}
