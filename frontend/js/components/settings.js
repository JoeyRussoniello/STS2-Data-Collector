export function renderSettings(container, api) {
  const current = api.getBaseUrl();

  container.innerHTML = `
    <div class="settings-group">
      <label class="settings-label">ARCHIVE ENDPOINT</label>
      <p class="text-dim">The archive API connection configured by environment.</p>
      <code class="settings-code">${current}</code>
    </div>

    <div class="settings-actions">
      <button class="btn btn--ghost" id="btn-test-connection">Test Connection</button>
    </div>
    <div id="settings-status" class="settings-status"></div>
  `;

  document.getElementById('btn-test-connection').addEventListener('click', async () => {
    const status = document.getElementById('settings-status');
    const testUrl = api.getBaseUrl();

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
