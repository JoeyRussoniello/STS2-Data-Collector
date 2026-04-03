import { api } from './api.js';
import { renderOverview } from './pages/overview.js';
import { renderCharacters } from './pages/characters.js';
import { renderCards } from './pages/cards.js';
import { renderRelics } from './pages/relics.js';
import { renderSettings, updateApiIndicator } from './components/settings.js';

const pages = {
  overview: renderOverview,
  characters: renderCharacters,
  cards: renderCards,
  relics: renderRelics,
};

function parseHash() {
  const raw = location.hash.replace('#', '') || 'overview';
  const slash = raw.indexOf('/');
  if (slash === -1) return { page: raw, steamId: null };
  return { page: raw.slice(0, slash), steamId: raw.slice(slash + 1) || null };
}

function updatePlayerScope(steamId) {
  const scope = document.getElementById('player-scope');
  const content = document.getElementById('content');
  const input = document.getElementById('steam-id-input');
  if (steamId) {
    scope.style.display = 'flex';
    document.getElementById('scope-steam-id').textContent = steamId;
    content.style.paddingTop = '76px';
    if (input) input.value = steamId;
  } else {
    scope.style.display = 'none';
    content.style.paddingTop = '';
    if (input) input.value = '';
  }
}

function navigate() {
  const { page, steamId } = parseHash();
  if (!pages[page]) { location.hash = steamId ? `#overview/${steamId}` : '#overview'; return; }

  document.querySelectorAll('.nav-link').forEach(l => {
    l.classList.toggle('active', l.dataset.page === page);
    l.href = steamId ? `#${l.dataset.page}/${steamId}` : `#${l.dataset.page}`;
  });

  updatePlayerScope(steamId);

  const content = document.getElementById('content');
  content.classList.add('fade-out');

  setTimeout(() => {
    pages[page](content, api, steamId);
    content.classList.remove('fade-out');
  }, 150);
}

function initSettings() {
  const overlay = document.getElementById('modal-overlay');

  document.getElementById('btn-settings').addEventListener('click', () => {
    renderSettings(document.getElementById('settings-body'), api);
    overlay.classList.add('visible');
  });

  document.getElementById('btn-close-modal').addEventListener('click', () =>
    overlay.classList.remove('visible')
  );

  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('visible');
  });
}

function initSteamIdInput() {
  const input = document.getElementById('steam-id-input');
  const goBtn = document.getElementById('steam-id-go');
  const clearBtn = document.getElementById('scope-clear');

  function applySteamId() {
    const id = input.value.trim();
    const { page } = parseHash();
    location.hash = id ? `#${page}/${id}` : `#${page}`;
  }

  goBtn?.addEventListener('click', applySteamId);
  input?.addEventListener('keydown', e => { if (e.key === 'Enter') applySteamId(); });
  clearBtn?.addEventListener('click', e => {
    e.preventDefault();
    if (input) input.value = '';
    const { page } = parseHash();
    location.hash = `#${page}`;
  });
}

window.addEventListener('hashchange', navigate);
window.addEventListener('DOMContentLoaded', () => {
  initSettings();
  initSteamIdInput();
  updateApiIndicator(api);
  navigate();
});
