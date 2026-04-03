export function renderSettings(container, api) {
  const current = api.getBaseUrl();
  const isLocal = /localhost|127\.0\.0\.1/.test(current);
  const savedProd = localStorage.getItem('sts2_prod_url') || '';

  container.innerHTML = `
    <div class="settings-group">
      <label class="settings-label">API ENDPOINT</label>
      <div class="settings-options">
        <label class="radio-option ${isLocal ? 'selected' : ''}">
          <input type="radio" name="api-mode" value="local" ${isLocal ? 'checked' : ''}>
          <span class="radio-text">Local Development</span>
          <span class="radio-desc">http://localhost:8000</span>
        </label>
        <label class="radio-option ${!isLocal ? 'selected' : ''}">
          <input type="radio" name="api-mode" value="production" ${!isLocal ? 'checked' : ''}>
          <span class="radio-text">Production Server</span>
          <span class="radio-desc">Remote API endpoint</span>
        </label>
      </div>
    </div>

    <div class="settings-group" id="prod-url-group" style="display:${!isLocal ? 'block' : 'none'}">
      <label class="settings-label">PRODUCTION URL</label>
      <input type="text" class="settings-input" id="prod-url"
             value="${!isLocal ? current : savedProd}"
             placeholder="https://your-api.example.com">
    </div>

    <div class="settings-actions">
      <button class="btn btn--primary" id="btn-save-settings">Apply &amp; Reconnect</button>
      <button class="btn btn--ghost" id="btn-test-connection">Test Connection</button>
    </div>
    <div id="settings-status" class="settings-status"></div>
  `;

  container.querySelectorAll('input[name="api-mode"]').forEach(radio => {
    radio.addEventListener('change', () => {
      document.getElementById('prod-url-group').style.display =
        radio.value === 'production' ? 'block' : 'none';
      container.querySelectorAll('.radio-option').forEach(o => o.classList.remove('selected'));
      radio.closest('.radio-option').classList.add('selected');
    });
  });

  document.getElementById('btn-save-settings').addEventListener('click', () => {
    const mode = container.querySelector('input[name="api-mode"]:checked').value;
    if (mode === 'local') {
      api.setBaseUrl('http://localhost:8000');
    } else {
      const url = document.getElementById('prod-url').value.trim();
      if (!url) {
        document.getElementById('settings-status').innerHTML =
          '<span class="status-error">Enter a production URL</span>';
        return;
      }
      localStorage.setItem('sts2_prod_url', url);
      api.setBaseUrl(url);
    }
    updateApiIndicator(api);
    document.getElementById('modal-overlay').classList.remove('visible');
    location.reload();
  });

  document.getElementById('btn-test-connection').addEventListener('click', async () => {
    const status = document.getElementById('settings-status');
    const mode = container.querySelector('input[name="api-mode"]:checked').value;
    const testUrl = mode === 'local'
      ? 'http://localhost:8000'
      : document.getElementById('prod-url').value.trim();

    if (!testUrl) { status.innerHTML = '<span class="status-error">Enter a URL first</span>'; return; }

    status.innerHTML = '<span class="status-testing">Testing connection…</span>';
    try {
      const r = await fetch(`${testUrl}/health`);
      status.innerHTML = r.ok
        ? '<span class="status-ok">✦ Connection established. The Archive responds.</span>'
        : `<span class="status-error">Archive returned ${r.status}</span>`;
    } catch (e) {
      status.innerHTML = `<span class="status-error">Cannot reach Archive: ${e.message}</span>`;
    }
  });
}

export function updateApiIndicator(api) {
  const dot = document.getElementById('api-dot');
  const label = document.getElementById('api-label');
  const url = api.getBaseUrl();
  const isLocal = /localhost|127\.0\.0\.1/.test(url);

  label.textContent = isLocal ? 'Local API' : 'Production';

  fetch(`${url}/health`).then(r => {
    dot.className = 'api-dot ' + (r.ok ? 'connected' : 'disconnected');
    if (r.ok) label.textContent = isLocal ? 'Local — Connected' : 'Production — Connected';
  }).catch(() => {
    dot.className = 'api-dot disconnected';
    label.textContent = isLocal ? 'Local — Offline' : 'Production — Offline';
  });
}
