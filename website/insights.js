(() => {
  const status = document.getElementById('insights-status');
  const content = document.getElementById('insights-content');
  const healthMessage = document.getElementById('health-status-message');
  const healthCard = document.getElementById('health-card');

  async function api(path, method = 'GET', payload) {
    const response = await fetch(path, {
      method, credentials: 'same-origin', cache: 'no-store',
      ...(payload ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) } : {}),
    });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) { location.replace('login.html'); throw new Error('Please log in again.'); }
    if (!response.ok) throw new Error(result.error || 'MHM could not load this information.');
    return result;
  }

  function text(tag, value, className) {
    const node = document.createElement(tag);
    node.textContent = value;
    if (className) node.className = className;
    return node;
  }

  function number(value, fallback = '—') {
    return Number.isFinite(Number(value)) ? String(value) : fallback;
  }

  function metric(label, value, note = '') {
    const card = text('article', '', 'card insight-metric');
    card.append(text('span', label, 'eyebrow'), text('strong', value));
    if (note) card.append(text('p', note));
    return card;
  }

  function message(container, value) {
    container.replaceChildren(text('p', value, 'field-hint'));
  }

  function renderInsights(data) {
    const summary = document.getElementById('insights-summary');
    const total = data.available?.total_checkins ?? data.wellness?.total_checkins ?? 0;
    const wellness = data.wellness?.score ?? data.wellness?.wellness_score;
    summary.replaceChildren(
      metric('Check-ins', number(total, '0'), `Last ${data.days} days`),
      metric('Wellness score', number(wellness), data.wellness?.interpretation || 'Shown when enough data is available'),
      metric('Completion', data.completion?.rate == null ? '—' : `${data.completion.rate}%`, `${data.completion?.days_completed || 0} completed check-ins`),
      metric('Mood trend', data.mood?.trend || 'Not enough data', data.mood?.average_mood == null ? '' : `Average ${data.mood.average_mood}`),
    );

    const moodEnergy = document.getElementById('mood-energy');
    moodEnergy.replaceChildren();
    if (data.mood?.error && data.energy?.error) message(moodEnergy, 'Complete a few check-ins to see mood and energy patterns here.');
    else {
      if (!data.mood?.error) moodEnergy.append(text('p', `Mood averaged ${number(data.mood.average_mood)} with a ${data.mood.trend || 'stable'} trend.`));
      if (!data.energy?.error) moodEnergy.append(text('p', `Energy averaged ${number(data.energy.average_energy)} with a ${data.energy.trend || 'stable'} trend.`));
      const quantitative = data.quantitative && !data.quantitative.error ? data.quantitative : {};
      const list = document.createElement('ul');
      for (const [key, value] of Object.entries(quantitative)) list.append(text('li', `${key.replaceAll('_', ' ')}: ${number(value.average)} average (${value.count || 0} responses)`));
      if (list.children.length) moodEnergy.append(list);
    }

    const sleepHabits = document.getElementById('sleep-habits');
    sleepHabits.replaceChildren();
    if (!data.sleep?.error) sleepHabits.append(text('p', `Average sleep: ${number(data.sleep.average_hours)} hours. Average quality: ${number(data.sleep.average_quality)}.`));
    const habitStats = data.habits?.habit_stats || data.habits?.habits || {};
    const habitList = document.createElement('ul');
    for (const [key, value] of Object.entries(habitStats)) {
      const rate = value.completion_rate ?? value.rate;
      habitList.append(text('li', `${key.replaceAll('_', ' ')}${rate == null ? '' : `: ${rate}%`}`));
    }
    if (habitList.children.length) sleepHabits.append(habitList);
    if (data.sleep?.error && !habitList.children.length) message(sleepHabits, 'Sleep and habit patterns will appear after they are included in your check-ins.');

    const history = document.getElementById('checkin-history');
    history.replaceChildren();
    if (!data.history?.length) message(history, 'No saved check-ins in this period.');
    else {
      const list = text('div', '', 'history-list');
      for (const entry of data.history.slice(0, 20)) {
        const row = text('article', '', 'history-row');
        row.append(text('strong', entry.date || 'Saved check-in'));
        const values = Object.entries(entry).filter(([key]) => !['date', 'timestamp', 'questions_asked'].includes(key)).slice(0, 6);
        row.append(text('span', values.length ? values.map(([key, value]) => `${key.replaceAll('_', ' ')}: ${String(value)}`).join(' · ') : 'Check-in saved'));
        list.append(row);
      }
      history.append(list);
    }
    content.hidden = false;
  }

  async function loadInsights() {
    status.textContent = 'Loading your insights…';
    status.classList.remove('is-error');
    try {
      const data = await api(`/api/insights?days=${document.getElementById('insights-days').value}`);
      renderInsights(data);
      status.textContent = '';
    } catch (error) { status.textContent = error.message; status.classList.add('is-error'); }
  }

  function renderHealth(data) {
    document.getElementById('health-feature-state').textContent = data.feature_state;
    document.getElementById('health-connected').textContent = data.connected ? 'Yes' : 'No';
    document.getElementById('health-last-sync').textContent = data.last_success_at || 'Never';
    document.getElementById('health-connect').hidden = data.connected;
    document.getElementById('health-connect').disabled = !data.connect_available || data.connecting;
    document.getElementById('health-enable').hidden = !data.connected || data.feature_state === 'enabled';
    document.getElementById('health-pause').hidden = data.feature_state !== 'enabled';
    document.getElementById('health-sync').hidden = !data.connected;
    document.getElementById('health-delete').hidden = !data.connected && data.feature_state === 'disabled';
    document.getElementById('health-guidance').textContent = data.connecting ? 'Finish approving access in the Google window, then refresh this page.'
      : data.has_recent_error ? 'A recent sync had an issue. Your normal MHM messages continue while it is resolved.'
        : !data.connect_available && !data.connected ? data.connect_error || 'Google Health connection is not configured.'
          : 'MHM uses read-only health data for personalization. You can pause or delete it here at any time.';
    healthCard.hidden = false;
    healthMessage.textContent = '';
  }

  async function loadHealth() {
    try { renderHealth(await api('/api/health')); }
    catch (error) { healthMessage.textContent = error.message; healthMessage.classList.add('is-error'); }
  }

  async function healthAction(action) {
    healthMessage.textContent = action === 'sync' ? 'Syncing…' : 'Saving…';
    healthMessage.classList.remove('is-error');
    try {
      const result = await api('/api/health', 'POST', { action });
      if (result.url) window.open(result.url, '_blank', 'noopener,noreferrer');
      renderHealth(result);
      healthMessage.textContent = result.message || (result.url ? 'Google Health opened in a new tab.' : 'Saved.');
    } catch (error) { healthMessage.textContent = error.message; healthMessage.classList.add('is-error'); }
  }

  document.getElementById('insights-days').addEventListener('change', loadInsights);
  document.getElementById('insights-refresh').addEventListener('click', loadInsights);
  for (const action of ['connect', 'enable', 'pause', 'sync']) document.getElementById(`health-${action}`).addEventListener('click', () => healthAction(action));
  document.getElementById('health-delete').addEventListener('click', () => {
    if (window.confirm('Delete all locally stored Google Health data and disable the integration? This cannot be undone.')) healthAction('delete');
  });
  loadInsights();
  loadHealth();
})();
