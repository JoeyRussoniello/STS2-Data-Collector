function fmt(id) {
  return id.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/\b\w/g, c => c.toUpperCase());
}
function pct(v) { return (v * 100).toFixed(1) + '%'; }
function wrColor(rate) {
  if (rate >= 0.55) return 'var(--secondary)';
  if (rate >= 0.40) return 'var(--primary)';
  return 'var(--tertiary-dim)';
}

export async function renderRelics(el, api, steamId = null) {
  el.innerHTML = '<div class="loading-state"><div class="eldritch-spinner"></div><p>Channeling relic frequencies…</p></div>';

  try {
    const [relics, encounters] = await Promise.all([
      api.getRelics({ min_appearances: 3, steam_id: steamId }),
      api.getEncounters({ steam_id: steamId }),
    ]);

    el.innerHTML = `
      <div class="page-header">
        <h1>Relic &amp; Encounter Analysis</h1>
        <p class="page-header__desc">${steamId
          ? 'Relic and encounter data scoped to this player\u2019s ascents.'
          : 'Visualizing the metaphysical patterns of failure and fortune across all recent spire ascents.'}</p>
      </div>

      <div class="filter-bar" id="relic-filters">
        <div class="filter-group">
          <label class="filter-label">Character</label>
          <select class="filter-select" id="relic-char">
            <option value="">All Characters</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Ascension</label>
          <select class="filter-select" id="relic-asc">
            <option value="">All Levels</option>
            ${Array.from({length: 21}, (_, i) => `<option value="${i}">Ascension ${i}</option>`).join('')}
          </select>
        </div>
        <button class="filter-btn" id="relic-apply">Apply Filters</button>
      </div>

      <!-- Relic Leaderboard -->
      <div class="panel">
        <h3 class="panel__title">✦ Relic Win-Rate Leaderboard</h3>
        <div id="relic-board" class="relic-board"></div>
      </div>

      <div class="section-divider"></div>

      <!-- Encounter Lethality -->
      <div class="panel">
        <h3 class="panel__title">💀 Lethality Index</h3>
        <p class="page-header__desc mb-lg" style="padding-left:0">Encounters ranked by total player kills. The Spire's most merciless guardians.</p>
        <div id="encounter-list"></div>
      </div>
    `;

    // Populate character dropdown
    try {
      const chars = await api.getCharacters();
      const sel = document.getElementById('relic-char');
      chars.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.character;
        opt.textContent = fmt(c.character);
        sel.appendChild(opt);
      });
    } catch (_) {}

    renderRelicBoard(relics);
    renderEncounterList(encounters);

    document.getElementById('relic-apply').addEventListener('click', async () => {
      const boardEl = document.getElementById('relic-board');
      const encEl = document.getElementById('encounter-list');
      boardEl.innerHTML = '<div class="loading-state"><div class="eldritch-spinner"></div></div>';
      encEl.innerHTML = '';
      try {
        const opts = {
          steam_id: steamId,
          character: document.getElementById('relic-char').value || undefined,
          ascension: document.getElementById('relic-asc').value || undefined,
        };
        const [r, e] = await Promise.all([
          api.getRelics({ ...opts, min_appearances: 3 }),
          api.getEncounters(opts),
        ]);
        renderRelicBoard(r);
        renderEncounterList(e);
      } catch (e) {
        boardEl.innerHTML = `<div class="error-state"><p>${e.message}</p></div>`;
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

function renderRelicBoard(relics) {
  const board = document.getElementById('relic-board');
  if (!relics.length) {
    board.innerHTML = '<div class="empty-state"><p>No relic data found for current filters.</p></div>';
    return;
  }

  const sorted = [...relics].sort((a, b) => b.win_rate_when_present - a.win_rate_when_present);
  const featured = sorted[0];
  const rest = sorted.slice(1);

  board.innerHTML = `
    <div class="relic-card relic-card--featured">
      <div style="font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--secondary);margin-bottom:4px;font-weight:700">Top Performer</div>
      <div class="relic-card__name" style="font-size:1.5rem">${fmt(featured.relic_id)}</div>
      <div class="relic-card__meta">${featured.times_present.toLocaleString()} appearances · Avg floor ${featured.avg_floor_acquired.toFixed(1)}</div>
      <div class="relic-card__wr" style="color:${wrColor(featured.win_rate_when_present)}">${pct(featured.win_rate_when_present)}</div>
      <div class="relic-card__wr-label">Net Win Rate</div>
      <div class="relic-card__chars">
        ${(featured.characters || []).map(c => `<span class="relic-char-chip">${fmt(c.character)} (${c.count})</span>`).join('')}
      </div>
    </div>
    ${rest.slice(0, 11).map((r, i) => `
      <div class="relic-card">
        <div class="relic-card__name">${fmt(r.relic_id)}</div>
        <div class="relic-card__meta">${r.times_present.toLocaleString()} appearances · Floor ${r.avg_floor_acquired.toFixed(1)}</div>
        <div class="relic-card__wr" style="color:${wrColor(r.win_rate_when_present)}">${pct(r.win_rate_when_present)}</div>
        <div class="relic-card__wr-label">Win Rate</div>
        <div class="relic-card__chars">
          ${(r.characters || []).map(c => `<span class="relic-char-chip">${fmt(c.character)} (${c.count})</span>`).join('')}
        </div>
      </div>
    `).join('')}
  `;
}

function renderEncounterList(encounters) {
  const list = document.getElementById('encounter-list');
  if (!encounters.length) {
    list.innerHTML = '<div class="empty-state"><p>No encounter data for current filters.</p></div>';
    return;
  }

  const sorted = [...encounters].sort((a, b) => b.kill_count - a.kill_count);
  const maxKills = sorted[0]?.kill_count || 1;

  list.innerHTML = sorted.slice(0, 15).map((e, i) => `
    <div class="encounter-row">
      <span class="killer-rank">${i + 1}</span>
      <span class="encounter-name">${fmt(e.encounter)}</span>
      <div class="encounter-bar"><div class="encounter-bar__fill" style="width:${(e.kill_count / maxKills) * 100}%"></div></div>
      <span class="encounter-kills">${e.kill_count.toLocaleString()} kills</span>
      <span class="encounter-share">${pct(e.kill_share)}</span>
      <div class="encounter-chars">
        ${(e.characters || []).slice(0, 3).map(c => `<span class="relic-char-chip">${fmt(c.character)}: ${c.kill_count}</span>`).join('')}
      </div>
    </div>
  `).join('');
}
