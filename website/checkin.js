(() => {
  const status = document.getElementById('checkin-status');
  const panel = document.getElementById('checkin-panel');
  const progress = document.getElementById('checkin-progress');
  const message = document.getElementById('checkin-message');
  const off = document.getElementById('checkin-off');
  const start = document.getElementById('checkin-start');
  const form = document.getElementById('checkin-form');
  const answer = document.getElementById('checkin-answer');

  function showStatus(text, error = false) {
    status.textContent = text;
    status.classList.toggle('is-error', error);
  }

  async function api(path, method = 'GET', payload) {
    const response = await fetch(path, {
      method,
      credentials: 'same-origin',
      cache: 'no-store',
      ...(payload === undefined ? {} : {
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
    });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) {
      window.dispatchEvent(new Event('mhm:signed-out'));
      location.replace('login.html');
      throw new Error('Please log in again.');
    }
    if (!response.ok) throw new Error(result.error || 'MHM could not continue that check-in. Please try again.');
    return result;
  }

  function show(result) {
    panel.hidden = false;
    message.textContent = result.enabled === false
      ? ''
      : (result.message || (result.active ? '' : 'When you are ready, start a short check-in.'));
    progress.textContent = result.active && result.index && result.total ? `Question ${result.index} of ${result.total}` : '';
    off.hidden = result.enabled !== false;
    start.hidden = result.active || result.completed_today || result.enabled === false;
    form.hidden = !result.active;
    if (!result.active) answer.value = '';
    showStatus('');
  }

  async function send(payload) {
    showStatus(payload.action === 'start' ? 'Starting your check-in…' : 'Saving…');
    try {
      show(await api('/api/checkins', 'POST', payload));
      if (!form.hidden) answer.focus();
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  start.addEventListener('click', () => send({ action: 'start' }));
  form.addEventListener('submit', event => {
    event.preventDefault();
    send({ action: 'answer', answer: answer.value.trim() });
  });
  document.getElementById('checkin-skip').addEventListener('click', () => send({ action: 'skip' }));
  document.getElementById('checkin-cancel').addEventListener('click', () => {
    if (window.confirm('Cancel this check-in? Answers so far will not be saved.')) send({ action: 'cancel' });
  });

  api('/api/checkins').then(show).catch(error => {
    panel.hidden = true;
    showStatus(error.message, true);
  });
})();
