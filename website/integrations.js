(() => {
  const healthMessage = document.getElementById('health-status-message');
  const healthCard = document.getElementById('health-card');
  const healthButtons = ['connect', 'enable', 'pause', 'sync', 'delete'].map(action => document.getElementById(`health-${action}`));
  let healthBusy = false;

  async function api(path, method = 'GET', payload) {
    const response = await fetch(path, {
      method, credentials: 'same-origin', cache: 'no-store',
      ...(payload ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) } : {}),
    });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) { window.dispatchEvent(new Event('mhm:signed-out')); location.replace('login.html'); throw new Error('Please log in again.'); }
    if (!response.ok) throw new Error(result.error || 'MHM could not load this information.');
    return result;
  }

  function renderHealth(data) {
    document.getElementById('health-feature-state').textContent = data.feature_state;
    document.getElementById('health-connected').textContent = data.connected ? 'Yes' : 'No';
    document.getElementById('health-last-sync').textContent = data.last_success_at || 'Never';
    document.getElementById('health-connect').hidden = data.connected;
    document.getElementById('health-connect').disabled = healthBusy || !data.connect_available || data.connecting;
    document.getElementById('health-enable').hidden = !data.connected || data.feature_state === 'enabled';
    document.getElementById('health-pause').hidden = data.feature_state !== 'enabled';
    document.getElementById('health-sync').hidden = !data.connected;
    document.getElementById('health-delete').hidden = !data.connected && data.feature_state === 'disabled';
    for (const button of healthButtons.slice(1)) button.disabled = healthBusy;
    document.getElementById('health-guidance').textContent = data.connecting ? 'Finish approving access in the Google window, then refresh this page.'
      : data.has_recent_error ? 'A recent sync had an issue. Your normal MHM messages continue while it is resolved.'
        : !data.connect_available && !data.connected ? data.connect_error || 'Google Health connection is not configured.'
          : 'MHM uses read-only health data for personalization. You can pause or delete it here at any time.';
    healthCard.hidden = false;
    healthMessage.textContent = '';
  }

  async function loadHealth() {
    try { renderHealth(await api('/api/health')); healthMessage.classList.remove('is-error'); }
    catch (error) { healthMessage.textContent = error.message; healthMessage.classList.add('is-error'); }
  }

  function setHealthBusy(busy) {
    healthBusy = busy;
    for (const button of healthButtons) button.disabled = busy;
    if (busy) healthCard.setAttribute('aria-busy', 'true');
    else healthCard.removeAttribute('aria-busy');
  }

  async function healthAction(action) {
    if (healthBusy) return;
    setHealthBusy(true);
    healthMessage.textContent = action === 'sync' ? 'Syncing…' : 'Saving…';
    healthMessage.classList.remove('is-error');
    try {
      const result = await api('/api/health', 'POST', { action });
      if (result.url) {
        const opened = window.open(result.url, '_blank');
        if (opened) opened.opener = null;
        else location.assign(result.url);
      }
      setHealthBusy(false);
      renderHealth(result);
      healthMessage.textContent = result.message || (result.url ? 'Google Health opened in a new tab.' : 'Saved.');
    } catch (error) {
      setHealthBusy(false);
      healthMessage.textContent = error.message;
      healthMessage.classList.add('is-error');
    }
  }

  for (const action of ['connect', 'enable', 'pause', 'sync']) document.getElementById(`health-${action}`).addEventListener('click', () => healthAction(action));
  document.getElementById('health-delete').addEventListener('click', () => {
    if (window.confirm('Delete all locally stored Google Health data and disable the integration? This cannot be undone.')) healthAction('delete');
  });
  loadHealth();
})();
