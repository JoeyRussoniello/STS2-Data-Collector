const DEFAULT_LOCAL_URL = 'http://localhost:8080';

class ApiClient {
  constructor() {
    this.baseUrl = localStorage.getItem('sts2_api_url') || DEFAULT_LOCAL_URL;
  }

  setBaseUrl(url) {
    this.baseUrl = url.replace(/\/+$/, '');
    localStorage.setItem('sts2_api_url', this.baseUrl);
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
export { DEFAULT_LOCAL_URL };

