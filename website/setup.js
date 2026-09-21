(() => {
  const status = document.getElementById('setup-status');
  const setupContent = document.getElementById('setup-content');
  const continueButton = document.getElementById('setup-continue');
  const skipButton = document.getElementById('setup-skip');
  const setupForm = document.getElementById('setup-form');
  let settings;
  let step = 1;

  function returnToLogin() {
    window.dispatchEvent(new Event('mhm:signed-out'));
    location.replace('login.html');
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
      returnToLogin();
      throw new Error('Please log in again.');
    }
    if (!response.ok) throw new Error(result.error || 'MHM could not save that just now. Please try again.');
    return result;
  }

  function showStatus(message, error = false) {
    status.textContent = message;
    status.classList.toggle('is-error', error);
  }

  function defaultWindow(start, end) {
    return { 'Window 1': { active: true, days: ['ALL'], start_time: start, end_time: end } };
  }

  function withWindow(periods, start, end) {
    return periods && Object.keys(periods).length ? periods : defaultWindow(start, end);
  }

  function showStep(next) {
    step = next;
    document.getElementById('step-1').hidden = step !== 1;
    document.getElementById('step-2').hidden = step !== 2;
    document.getElementById('step-3').hidden = step !== 3;
    for (const index of [1, 2, 3]) {
      document.getElementById(`progress-${index}`).classList.toggle('is-current', index === step);
    }
    continueButton.textContent = step === 3 ? 'Finish →' : 'Continue →';
    skipButton.hidden = step !== 3;
  }

  async function saveSection(section, values) {
    settings = await api('/api/settings', 'POST', {
      section,
      revision: settings.revisions[section],
      values,
    });
  }

  function messageValues(enabled) {
    const current = { ...settings.sections.messages, enabled };
    if (!enabled) return current;
    const available = settings.options.categories || [];
    const categories = current.categories.length
      ? current.categories
      : [available.includes('motivational') ? 'motivational' : available[0]].filter(Boolean);
    if (!categories.length) {
      throw new Error('Message categories are not available yet. You can turn messages on later in Account.');
    }
    const periods = {};
    for (const category of categories) {
      periods[category] = withWindow(
        (current.periods || {})[category] || (settings.available_message_periods || {})[category],
        '18:00',
        '20:00',
      );
    }
    return { ...current, categories, periods };
  }

  function taskValues(enabled) {
    const current = { ...settings.sections.tasks, enabled };
    if (enabled) current.periods = withWindow(current.periods, '15:00', '17:00');
    return current;
  }

  function checkinValues(enabled) {
    const current = { ...settings.sections.checkins, enabled };
    if (enabled) current.periods = withWindow(current.periods, '09:30', '11:30');
    return current;
  }

  async function saveYou() {
    const name = document.getElementById('preferred-name').value.trim();
    const timezone = document.getElementById('timezone').value;
    await saveSection('profile', { ...settings.sections.profile, preferred_name: name });
    await saveSection('delivery', { ...settings.sections.delivery, timezone });
  }

  async function saveSupport() {
    let messages = document.getElementById('enable-messages').checked;
    let tasks = document.getElementById('enable-tasks').checked;
    const checkins = document.getElementById('enable-checkins').checked;
    if (!messages && !tasks && !checkins) {
      tasks = true;
      document.getElementById('enable-tasks').checked = true;
      showStatus('I’ll keep task reminders on so you have a next step.');
    }
    if (messages) {
      try {
        await saveSection('messages', messageValues(true));
      } catch (error) {
        messages = false;
        document.getElementById('enable-messages').checked = false;
        showStatus(error.message, true);
      }
    } else {
      await saveSection('messages', messageValues(false));
    }
    await saveSection('tasks', taskValues(tasks));
    try {
      await saveSection('checkins', checkinValues(checkins));
    } catch (error) {
      if (!checkins) throw error;
      document.getElementById('enable-checkins').checked = false;
      showStatus(error.message, true);
    }
  }

  async function saveFirstTask() {
    const title = document.getElementById('first-task').value.trim();
    if (!title) return;
    await api('/api/tasks', 'POST', { title });
  }

  function goHome() {
    location.assign('home.html');
  }

  async function loadSetup() {
    if (!setupContent) return;
    try {
      const account = await api('/api/account');
      if (!account.needs_setup) {
        goHome();
        return;
      }
      settings = await api('/api/settings');
      document.getElementById('preferred-name').value = settings.sections.profile.preferred_name || account.preferred_name || '';
      const timezone = document.getElementById('timezone');
      const zones = settings.options.timezones || [];
      const selected = account.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/Regina';
      timezone.replaceChildren();
      for (const zone of zones) {
        const option = document.createElement('option');
        option.value = zone;
        option.textContent = zone.replaceAll('_', ' ');
        if (zone === selected) option.selected = true;
        timezone.append(option);
      }
      if (!timezone.value && zones.length) timezone.value = zones[0];
      const canMessage = (settings.options.categories || []).length > 0;
      document.getElementById('enable-messages').disabled = !canMessage;
      document.getElementById('enable-messages').checked = canMessage;
      setupContent.hidden = false;
      showStep(1);
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  if (setupForm) setupForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (continueButton.disabled) return;
    continueButton.disabled = true;
    skipButton.disabled = true;
    continueButton.setAttribute('aria-busy', 'true');
    if (step !== 2) showStatus(step === 1 ? 'Saving…' : 'Finishing…');
    try {
      if (step === 1) {
        await saveYou();
        showStatus('');
        showStep(2);
      } else if (step === 2) {
        await saveSupport();
        showStep(3);
      } else {
        await saveFirstTask();
        goHome();
      }
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      continueButton.disabled = false;
      skipButton.disabled = false;
      continueButton.removeAttribute('aria-busy');
    }
  });

  if (skipButton) skipButton.addEventListener('click', () => {
    if (skipButton.disabled) return;
    goHome();
  });

  if (setupContent) loadSetup();
})();
