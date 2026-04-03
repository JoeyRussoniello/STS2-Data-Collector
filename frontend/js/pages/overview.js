// Shared helpers
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

export async function renderOverview(el, api, steamId = null) {
  el.innerHTML = '<div class="loading-state"><div class="eldritch-spinner"></div><p>Consulting the archives…</p></div>';

  try {
    const [overview, outcomes] = await Promise.all([
      api.getOverview(steamId),
      api.getRunOutcomes({ steam_id: steamId }),
    ]);

    const chars = overview.characters || [];
    const totalRuns = chars.reduce((s, c) => s + c.run_count, 0) || overview.run_count;
    const mostPopular = chars.length ? chars.reduce((a, b) => a.run_count > b.run_count ? a : b) : null;
    const bestWR = chars.length ? chars.reduce((a, b) => a.win_rate > b.win_rate ? a : b) : null;

    el.innerHTML = `
      <div class="page-header">
        <h1>${steamId ? 'Personal Player Ledger' : 'The Global Thread'}</h1>
        <p class="page-header__desc">${steamId
          ? 'Stats scoped to this player\u2019s recorded ascents. All metrics reflect individual performance.'
          : 'Aggregated data from all recorded spire ascents. Observe the cosmic balance of the Spire\u2019s second manifestation.'}</p>
      </div>

      <!-- Hero cards -->
      <div class="stat-cards">
        <div class="stat-card">
          <span class="stat-card__label">Total Runs Tracked</span>
          <span class="stat-card__value">${overview.run_count.toLocaleString()}</span>
          <span class="stat-card__footer secondary">${pct(overview.win_rate)} overall win rate</span>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">Most Popular Character</span>
          <span class="stat-card__value">${mostPopular ? fmt(mostPopular.character) : 'N/A'}</span>
          <span class="stat-card__footer primary">${mostPopular ? '★ ' + pct(mostPopular.run_count / totalRuns) + ' pick rate' : ''}</span>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">Highest Win Rate</span>
          <span class="stat-card__value">${bestWR ? pct(bestWR.win_rate) : 'N/A'}</span>
          <span class="stat-card__footer secondary">${bestWR ? fmt(bestWR.character) : ''}</span>
        </div>
      </div>

      <!-- Two-column mid section -->
      <div class="grid-2col">
        <div class="panel">
          <h3 class="panel__title">Character Playrate Distribution</h3>
          <div id="ov-char-bars"></div>
          <p class="panel__footnote">* Distribution reflects all recorded ascension levels.</p>
        </div>
        <div class="panel">
          <h3 class="panel__title">Acts Reached</h3>
          <div id="ov-acts-funnel"></div>
          <div class="acts-stats">
            <div>
              <span class="acts-stat__label">Avg. Run Time</span>
              <span class="acts-stat__value">${fmtTime(overview.avg_run_time_seconds)}</span>
            </div>
            <div>
              <span class="acts-stat__label">Avg. Ascension</span>
              <span class="acts-stat__value">${overview.avg_ascension.toFixed(1)}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom mini stats -->
      <div class="stat-cards">
        <div class="stat-card stat-card--compact">
          <span class="stat-card__label">Win Rate</span>
          <span class="stat-card__value text-secondary">${pct(overview.win_rate)}</span>
        </div>
        <div class="stat-card stat-card--compact">
          <span class="stat-card__label">Abandon Rate</span>
          <span class="stat-card__value text-tertiary">${pct(overview.abandon_rate)}</span>
        </div>
        <div class="stat-card stat-card--compact">
          <span class="stat-card__label">Avg Acts Cleared</span>
          <span class="stat-card__value">${overview.avg_acts_cleared.toFixed(1)}</span>
        </div>
        <div class="stat-card stat-card--compact">
          <span class="stat-card__label">Avg Ascension</span>
          <span class="stat-card__value text-primary">${overview.avg_ascension.toFixed(1)}</span>
        </div>
      </div>

      <!-- Deadliest Encounters -->
      ${outcomes.killed_by_encounter && outcomes.killed_by_encounter.length > 0 ? `
      <div class="section-divider"></div>
      <div class="panel">
        <h3 class="panel__title">💀 Deadliest Encounters</h3>
        <div id="ov-killers"></div>
      </div>` : ''}
    `;

    // Render character bars
    const barsEl = document.getElementById('ov-char-bars');
    const sorted = [...chars].sort((a, b) => b.run_count - a.run_count);
    barsEl.innerHTML = sorted.map(c => {
      const rate = totalRuns ? (c.run_count / totalRuns) : 0;
      return `<div class="char-bar">
        <div class="char-bar__header">
          <span class="char-bar__name">${fmt(c.character)}</span>
          <span class="char-bar__pct">${pct(rate)}</span>
        </div>
        <div class="char-bar__track"><div class="char-bar__fill" style="width:${rate * 100}%"></div></div>
      </div>`;
    }).join('');

    // Render acts funnel
    const actsEl = document.getElementById('ov-acts-funnel');
    if (outcomes.acts_reached && outcomes.acts_reached.length) {
      const actsSort = [...outcomes.acts_reached].sort((a, b) => b.count - a.count);
      const maxCount = actsSort[0]?.count || 1;
      actsEl.innerHTML = actsSort.slice(0, 5).map(a => {
        const label = a.acts.join(' → ');
        const frac = a.count / maxCount;
        return `<div class="acts-step" style="opacity:${0.4 + frac * 0.6}">${label}: ${pct(a.count / outcomes.total)}</div>`;
      }).join('');
    } else {
      actsEl.innerHTML = '<p class="text-dim">No act progression data available.</p>';
    }

    // Render killers
    const killEl = document.getElementById('ov-killers');
    if (killEl && outcomes.killed_by_encounter.length) {
      const top = outcomes.killed_by_encounter.slice(0, 8);
      const maxShare = top[0]?.share || 1;
      killEl.innerHTML = top.map((k, i) => `
        <div class="killer-row">
          <span class="killer-rank">${i + 1}</span>
          <span class="killer-name">${fmt(k.name)}</span>
          <div class="killer-bar-track"><div class="killer-bar-fill" style="width:${(k.share / maxShare) * 100}%"></div></div>
          <span class="killer-share">${pct(k.share)}</span>
        </div>
      `).join('');
    }
  } catch (err) {
    el.innerHTML = `<div class="error-state">
      <h2>Connection to the Archive Failed</h2>
      <p>${err.message}</p>
      <p class="text-dim">Check your API configuration in Settings (⚙).</p>
    </div>`;
  }
}
