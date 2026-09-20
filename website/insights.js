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
    const total = data.available?.total_checkins ?? 0;
    const wellness = data.wellness?.score;
    const moodCount = Number(data.mood?.total_checkins) || 0;
    const moodMinimum = Number(data.mood?.trend_minimum) || 14;
    const moodReady = data.mood?.trend_ready === true || moodCount >= moodMinimum;
    const moodValue = data.mood?.error ? 'No mood ratings' : moodReady ? data.mood.trend : 'Building trend';
    const moodNote = data.mood?.error
      ? 'Add mood to a check-in to see a trend'
      : moodReady
        ? `Average ${number(data.mood.average_mood)} · ${moodCount} ratings`
        : `${moodCount} of ${moodMinimum} mood ratings · average ${number(data.mood.average_mood)}`;
    summary.replaceChildren(
      metric('Check-ins', number(total, '0'), `Last ${data.days} days`),
      metric('Wellness score', number(wellness), data.wellness?.interpretation || 'Shown when enough data is available'),
      metric('Completion', data.completion?.rate == null ? '—' : `${data.completion.rate}%`, `${data.completion?.days_completed || 0} completed check-ins`),
      metric('Mood trend', moodValue, moodNote),
    );

    const moodEnergy = document.getElementById('mood-energy');
    moodEnergy.replaceChildren();
    if (data.mood?.error && data.energy?.error) message(moodEnergy, 'Complete a few check-ins to see mood and energy patterns here.');
    else {
      if (!data.mood?.error) moodEnergy.append(text('p', moodReady
        ? `Mood averaged ${number(data.mood.average_mood)} with a ${data.mood.trend || 'stable'} trend.`
        : `Mood averaged ${number(data.mood.average_mood)}. ${moodCount} of ${moodMinimum} mood ratings are available; the trend compares the latest 7 with the previous 7.`));
      if (!data.energy?.error) moodEnergy.append(text('p', `Energy averaged ${number(data.energy.average_energy)} with a ${data.energy.trend || 'stable'} trend.`));
      const moodValues = Array.isArray(data.mood?.recent_data) ? data.mood.recent_data.map(item => Number(item.mood)).filter(Number.isFinite) : [];
      if (moodValues.length) {
        const changes = moodValues.slice(1).filter((value, index) => value !== moodValues[index]).length;
        const high = moodValues.filter(value => value >= 4).length;
        const low = moodValues.filter(value => value <= 2).length;
        const details = document.createElement('ul');
        details.append(text('li', `Mood changes: ${changes}`), text('li', `High-mood days: ${high}`), text('li', `Low-mood days: ${low}`));
        if (data.mood.best_day) details.append(text('li', `Highest: ${number(data.mood.best_day.mood)} on ${data.mood.best_day.date}`));
        if (data.mood.worst_day) details.append(text('li', `Lowest: ${number(data.mood.worst_day.mood)} on ${data.mood.worst_day.date}`));
        moodEnergy.append(details);
      }
      const quantitative = data.quantitative && !data.quantitative.error ? data.quantitative : {};
      const list = document.createElement('ul');
      for (const [key, value] of Object.entries(quantitative)) list.append(text('li', `${key.replaceAll('_', ' ')}: ${number(value.average)} average (${value.count || 0} responses)`));
      if (list.children.length) moodEnergy.append(list);
    }

    const recommendations = document.getElementById('wellness-recommendations');
    recommendations.replaceChildren();
    const recommendationList = Array.isArray(data.wellness?.recommendations) ? data.wellness.recommendations : [];
    if (recommendationList.length) {
      const list = document.createElement('ul');
      for (const item of recommendationList) list.append(text('li', String(item)));
      recommendations.append(list);
    } else message(recommendations, 'Recommendations will appear when enough check-in data is available.');

    const sleep = document.getElementById('sleep-detail');
    sleep.replaceChildren();
    if (!data.sleep?.error) {
      sleep.append(text('p', `Average sleep: ${number(data.sleep.average_hours)} hours. Average quality: ${number(data.sleep.average_quality)}.`));
      const sleepStats = document.createElement('ul');
      sleepStats.append(
        text('li', `Good sleep days: ${data.sleep.good_sleep_days || 0}`),
        text('li', `Poor sleep days: ${data.sleep.poor_sleep_days || 0}`),
        text('li', `Sleep consistency: ${data.sleep.sleep_consistency == null ? '—' : `${number(data.sleep.sleep_consistency)}%`}`),
      );
      for (const item of Array.isArray(data.sleep.recommendations) ? data.sleep.recommendations : []) sleepStats.append(text('li', `Recommendation: ${item}`));
      sleep.append(sleepStats);
    } else message(sleep, 'Sleep patterns will appear after sleep is included in your check-ins.');

    const habits = document.getElementById('habit-detail');
    habits.replaceChildren();
    const habitStats = data.habits?.habits || {};
    const habitList = document.createElement('ul');
    let completedHabitDays = 0;
    let answeredHabitDays = 0;
    for (const [key, value] of Object.entries(habitStats)) {
      const rate = value.completion_rate;
      const completed = value.completed_days || 0;
      const answered = value.answered_days ?? 0;
      completedHabitDays += completed; answeredHabitDays += answered;
      habitList.append(text('li', `${value.name || key.replaceAll('_', ' ')}${rate == null ? '' : `: ${rate}%`} (${completed}/${answered} days)${value.status ? ` — ${value.status}` : ''}`));
    }
    if (habitList.children.length) {
      habits.append(text('p', `Overall completion: ${number(data.habits?.overall_completion, '0')}%. Completed ${completedHabitDays} of ${answeredHabitDays} recorded habit days.`), habitList);
    } else message(habits, 'Habit patterns will appear after yes/no habits are included in your check-ins.');

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
  document.getElementById('checkin-request').addEventListener('click', async () => {
    try {
      const result = await api('/api/actions', 'POST', { action: 'checkin_prompt' });
      status.textContent = result.message || 'Your check-in was queued.';
      status.classList.remove('is-error');
    } catch (error) { status.textContent = error.message; status.classList.add('is-error'); }
  });
  for (const action of ['connect', 'enable', 'pause', 'sync']) document.getElementById(`health-${action}`).addEventListener('click', () => healthAction(action));
  document.getElementById('health-delete').addEventListener('click', () => {
    if (window.confirm('Delete all locally stored Google Health data and disable the integration? This cannot be undone.')) healthAction('delete');
  });
  loadInsights();
  loadHealth();
})();
