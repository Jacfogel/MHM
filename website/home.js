(() => {
  const status = document.getElementById('app-status');
  const homeContent = document.getElementById('home-content');

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
    if (!response.ok) throw new Error(result.error || 'MHM could not load that just now. Please try again.');
    return result;
  }

  function nextTask(tasks) {
    const dated = [...tasks].filter(task => task.due_date).sort((left, right) => {
      const leftKey = `${left.due_date}T${left.due_time || '23:59'}`;
      const rightKey = `${right.due_date}T${right.due_time || '23:59'}`;
      return leftKey.localeCompare(rightKey);
    });
    return dated[0] || tasks[0] || null;
  }

  function dueLabel(task) {
    if (!task.due_date) return 'No due date — open it whenever you are ready.';
    return task.due_time ? `Due ${task.due_date} at ${task.due_time}.` : `Due ${task.due_date}.`;
  }

  function noteTitle(text) {
    const line = text.split(/\r?\n/).find(item => item.trim()) || 'Quick note';
    return line.trim().slice(0, 80);
  }

  function supportOn(account) {
    return Boolean(account.messages_enabled || account.tasks_enabled || account.checkins_enabled);
  }

  async function accountNeedsSetup(account) {
    if (account.needs_setup === true) return true;
    if (supportOn(account)) return false;
    if ('messages_enabled' in account && 'tasks_enabled' in account && 'checkins_enabled' in account) {
      return true;
    }
    try {
      const settings = await api('/api/settings');
      const sections = settings.sections || {};
      return !sections.messages?.enabled && !sections.tasks?.enabled && !sections.checkins?.enabled;
    } catch (error) {
      return account.needs_setup === true;
    }
  }

  async function loadHome() {
    if (!homeContent) return;
    try {
      const account = await api('/api/account');
      if (await accountNeedsSetup(account)) {
        location.replace('setup.html');
        return;
      }
      document.getElementById('home-name').textContent = account.preferred_name || 'there';
      document.getElementById('home-task-off').hidden = account.tasks_enabled;
      document.getElementById('home-checkin').hidden = !account.checkins_enabled;
      document.getElementById('home-checkin-answer').hidden = !account.checkins_enabled;
      document.getElementById('home-checkin-on').hidden = !account.checkins_enabled;
      document.getElementById('home-checkin-off').hidden = account.checkins_enabled;
      let checkinState = { active: false };
      if (account.checkins_enabled) {
        try {
          checkinState = await api('/api/checkins');
        } catch (error) {
          checkinState = { active: false };
        }
      }
      const checkinOn = document.getElementById('home-checkin-on');
      const answerLink = document.getElementById('home-checkin-answer');
      if (account.checkins_enabled && checkinState.active) {
        const progress = checkinState.index && checkinState.total ? ` Question ${checkinState.index} of ${checkinState.total}.` : '';
        checkinOn.textContent = `A check-in is open.${progress}`;
        answerLink.textContent = 'Continue check-in';
      } else {
        checkinOn.textContent = 'Answer here, or have MHM send one by email or Discord.';
        answerLink.textContent = 'Answer a check-in';
      }
      const tasks = await api('/api/tasks?status=active');
      const task = nextTask(tasks.tasks || []);
      document.getElementById('home-task-title').textContent = task ? task.title : 'No tasks yet.';
      document.getElementById('home-task-meta').textContent = task
        ? dueLabel(task)
        : 'Add something small on Tasks, or capture a thought below.';
      homeContent.hidden = false;
      status.textContent = '';
    } catch (error) {
      if (status) {
        status.textContent = error.message;
        status.classList.add('is-error');
      }
    }
  }

  const checkin = document.getElementById('home-checkin');
  if (checkin) checkin.addEventListener('click', async (event) => {
    const button = event.currentTarget;
    const checkinStatus = document.getElementById('home-checkin-status');
    if (button.disabled) return;
    button.disabled = true;
    checkinStatus.textContent = 'Queuing your check-in…';
    checkinStatus.classList.remove('is-error');
    try {
      const result = await api('/api/actions', 'POST', { action: 'checkin_prompt' });
      checkinStatus.textContent = result.message || 'Your check-in was queued for delivery.';
    } catch (error) {
      checkinStatus.textContent = error.message;
      checkinStatus.classList.add('is-error');
    } finally {
      button.disabled = false;
    }
  });

  const captureForm = document.getElementById('home-capture-form');
  if (captureForm) captureForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const note = document.getElementById('home-note');
    const button = document.getElementById('home-capture-submit');
    const captureStatus = document.getElementById('home-capture-status');
    const text = note.value.trim();
    if (!text) return;
    button.disabled = true;
    captureStatus.textContent = 'Saving…';
    captureStatus.classList.remove('is-error');
    try {
      await api('/api/notes', 'POST', { kind: 'note', title: noteTitle(text), description: text });
      note.value = '';
      captureStatus.textContent = 'Saved to your notebook.';
    } catch (error) {
      captureStatus.textContent = error.message;
      captureStatus.classList.add('is-error');
    } finally {
      button.disabled = false;
    }
  });

  if (homeContent) loadHome();
})();
