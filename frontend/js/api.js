const FALLBACK_API_URL = 'https://sts2-data-collector-production.up.railway.app';
const ENV_API_URL = globalThis.__STS2_API_URL__;

function normalizeBaseUrl(url) {
  return url.replace(/\/+$/, '');
}

class ApiClient {
  constructor() {
    const configuredUrl = typeof ENV_API_URL === 'string' ? ENV_API_URL.trim() : '';
    this.baseUrl = normalizeBaseUrl(configuredUrl || FALLBACK_API_URL);
  }

  getBaseUrl() {
    return this.baseUrl;
  }

  async request(path, params = {}) {
    const url = new URL(`${this.baseUrl}${path}`);
    for (const [k, v] of Object.entries(params)) {
      if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v);
    }
    const resp = await fetch(url.toString());
    if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
    return resp.json();
  }

  getOverview(steamId)          { return this.request('/api/stats/overview', { steam_id: steamId }); }
  getCharacters(opts = {})      { return this.request('/api/stats/characters', opts); }
  getCards(opts = {})            { return this.request('/api/stats/cards', opts); }
  getRelics(opts = {})           { return this.request('/api/stats/relics', opts); }
  getRunOutcomes(opts = {})      { return this.request('/api/stats/runs/outcomes', opts); }
  getEncounters(opts = {})       { return this.request('/api/stats/encounters', opts); }
  getDeckGrowth(opts = {})       { return this.request('/api/stats/deck/growth', opts); }
  listRuns(limit = 50, offset = 0) { return this.request('/api/runs', { limit, offset }); }
  checkHealth()                  { return this.request('/health'); }
}

export const api = new ApiClient();

