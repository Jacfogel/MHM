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

  function daysUntil(dueDate, now) {
    if (!dueDate || !/^\d{4}-\d{2}-\d{2}$/.test(dueDate)) return null;
    const [year, month, day] = dueDate.split('-').map(Number);
    const due = new Date(year, month - 1, day);
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    return Math.round((due.getTime() - today.getTime()) / 86400000);
  }

  function focusMeta(pick) {
    const { task, days, priority, recurring, minutes } = pick;
    const parts = [];
    if (minutes) parts.push(`About ${minutes} ${minutes === 1 ? 'minute' : 'minutes'}`);
    if (days === null) parts.push('No due date');
    else if (days < 0) parts.push(days === -1 ? 'Overdue by 1 day' : `Overdue by ${-days} days`);
    else if (days === 0) parts.push(task.due_time ? `Due today at ${task.due_time}` : 'Due today');
    else if (days === 1) parts.push('Due tomorrow');
    else parts.push(task.due_time ? `Due ${task.due_date} at ${task.due_time}` : `Due ${task.due_date}`);
    if (priority && priority !== 'medium') parts.push(`${priority.charAt(0).toUpperCase()}${priority.slice(1)} priority`);
    if (recurring) parts.push('Repeats');
    return parts.join(' · ');
  }

  function accountNeedsSetup(account) {
    return account.needs_setup === true;
  }

  let focusedTask = null;
  let suggestedSteps = [];
  let homeLoad = 0;
  let focusActionBusy = false;

  function renderFocus(result) {
    const focus = result && result.focus ? result.focus : null;
    focusedTask = focus ? focus.task : null;
    const pick = focusedTask ? {
      task: focusedTask,
      days: daysUntil(focusedTask.due_date, new Date()),
      priority: String(focusedTask.priority || 'medium').toLowerCase(),
      recurring: Boolean(focusedTask.recurrence && focusedTask.recurrence.pattern),
      minutes: Number.isFinite(Number(focus.effort_minutes)) ? Number(focus.effort_minutes) : null,
    } : null;
    const actions = document.getElementById('home-task-actions');
    const breakForm = document.getElementById('home-task-break-form');
    const breakButton = document.getElementById('home-task-break');
    const ownButton = document.getElementById('home-task-own');
    const stepTitle = document.getElementById('home-task-step-title');
    document.getElementById('home-task-title').textContent = focusedTask ? focusedTask.title : 'No tasks yet.';
    document.getElementById('home-task-meta').textContent = pick
      ? focusMeta(pick)
      : 'Add something small on Tasks, or tell MHM what you need.';
    const why = focus ? String(focus.reason || '') : '';
    const parentTitle = focus ? String(focus.parent_title || '') : '';
    document.getElementById('home-task-why').textContent = parentTitle ? `${why} Part of ${parentTitle}.` : why;
    if (actions) actions.hidden = !focusedTask;
    if (breakButton) breakButton.hidden = !focusedTask || Boolean(focusedTask.parent_id);
    if (ownButton) ownButton.hidden = !focusedTask || !focusedTask.parent_id;
    if (stepTitle) stepTitle.value = '';
    if (breakForm) breakForm.hidden = true;
    suggestedSteps = [];
    const taskStatus = document.getElementById('home-task-status');
    if (taskStatus) {
      taskStatus.textContent = '';
      taskStatus.classList.remove('is-error');
    }
  }

  async function loadHome() {
    if (!homeContent) return;
    try {
      const account = await api('/api/account');
      if (accountNeedsSetup(account)) {
        location.replace('setup.html');
        return;
      }
      document.getElementById('home-name').textContent = account.preferred_name || 'there';
      speakerName = (account.preferred_name || '').trim();
      document.querySelectorAll('.talk-you span').forEach(label => {
        label.textContent = speakerName || 'You';
      });
      document.getElementById('home-task-off').hidden = account.tasks_enabled;
      document.getElementById('home-checkin-off').hidden = account.checkins_enabled;
      const loadId = ++homeLoad;
      const focusPromise = api('/api/tasks/focus');
      const checkinPromise = account.checkins_enabled
        ? api('/api/checkins').catch(() => ({ active: false }))
        : Promise.resolve({ active: false });
      const [focus, loadedCheckin] = await Promise.all([focusPromise, checkinPromise]);
      if (loadId !== homeLoad) return;
      const checkinState = loadedCheckin || { active: false };
      const checkinOn = document.getElementById('home-checkin-on');
      const answerLink = document.getElementById('home-checkin-answer');
      const checkedIn = document.getElementById('home-checkin');
      checkinOn.hidden = true;
      answerLink.hidden = true;
      checkedIn.hidden = true;
      if (account.checkins_enabled && checkinState.active) {
        const progress = checkinState.index && checkinState.total ? ` Question ${checkinState.index} of ${checkinState.total}.` : '';
        checkinOn.hidden = false;
        checkinOn.textContent = `A check-in is open.${progress}`;
        answerLink.hidden = false;
        answerLink.textContent = 'Continue check-in';
      } else if (account.checkins_enabled && checkinState.completed_today) {
        checkedIn.hidden = false;
      } else if (account.checkins_enabled) {
        answerLink.hidden = false;
        answerLink.textContent = 'Start check-in';
      }
      renderFocus(focus);
      homeContent.hidden = false;
      pinTalkToLatest();
      window.requestAnimationFrame(pinTalkToLatest);
      status.textContent = '';
    } catch (error) {
      if (status) {
        status.textContent = error.message;
        status.classList.add('is-error');
      }
    }
  }

  function localStamp(now = new Date()) {
    const pad = value => String(value).padStart(2, '0');
    return {
      date: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`,
      time: `${pad(now.getHours())}:${pad(now.getMinutes())}`,
    };
  }

  function setFocusBusy(busy) {
    focusActionBusy = busy;
    const actions = document.getElementById('home-task-actions');
    if (actions) {
      if (busy) actions.setAttribute('aria-busy', 'true');
      else actions.removeAttribute('aria-busy');
    }
    const controls = document.querySelectorAll('#home-task-actions button, #home-task-break-save, #home-task-step-add');
    controls.forEach(control => { control.disabled = busy; });
  }

  async function runFocusAction(path, payload, pending) {
    if (!focusedTask || focusActionBusy) return;
    setFocusBusy(true);
    const taskId = focusedTask.id;
    const taskStatus = document.getElementById('home-task-status');
    if (taskStatus) {
      taskStatus.textContent = pending;
      taskStatus.classList.remove('is-error');
    }
    try {
      await api(`/api/tasks/${encodeURIComponent(taskId)}/${path}`, 'POST', payload);
      await loadHome();
    } catch (error) {
      if (taskStatus) {
        taskStatus.textContent = error.message;
        taskStatus.classList.add('is-error');
      }
    } finally {
      setFocusBusy(false);
    }
  }

  const doneButton = document.getElementById('home-task-done');
  if (doneButton) doneButton.addEventListener('click', () => {
    const stamp = localStamp();
    return runFocusAction('complete', { completion_date: stamp.date, completion_time: stamp.time, completion_notes: '' }, 'Marking done…');
  });
  const laterButton = document.getElementById('home-task-later');
  if (laterButton) laterButton.addEventListener('click', () => {
    return runFocusAction('snooze', { option: '1_hour' }, 'Setting this aside…');
  });
  function renderSuggestedSteps(steps) {
    suggestedSteps = steps.slice();
    const list = document.getElementById('home-task-steps');
    if (!list) return;
    list.replaceChildren();
    for (const step of steps) {
      const item = document.createElement('li');
      const label = document.createElement('label');
      const box = document.createElement('input');
      box.type = 'checkbox';
      box.checked = true;
      box.addEventListener('change', () => {
        suggestedSteps = box.checked
          ? [...suggestedSteps, step]
          : suggestedSteps.filter(item => item !== step);
      });
      const text = document.createElement('span');
      text.textContent = step;
      label.append(box, text);
      item.append(label);
      list.append(item);
    }
  }

  const breakButton = document.getElementById('home-task-break');
  const breakForm = document.getElementById('home-task-break-form');
  const breakSave = document.getElementById('home-task-break-save');
  if (breakButton && breakForm) breakButton.addEventListener('click', async () => {
    if (!focusedTask || focusActionBusy) return;
    setFocusBusy(true);
    const taskId = focusedTask.id;
    breakForm.hidden = false;
    suggestedSteps = [];
    renderSuggestedSteps([]);
    if (breakSave) breakSave.hidden = true;
    breakButton.disabled = true;
    const taskStatus = document.getElementById('home-task-status');
    if (taskStatus) {
      taskStatus.textContent = 'Looking for smaller steps…';
      taskStatus.classList.remove('is-error');
    }
    try {
      const result = await api(`/api/tasks/${encodeURIComponent(taskId)}/breakdown`, 'POST', {});
      const steps = (result.steps || []).filter(step => typeof step === 'string' && step.trim());
      if (!steps.length) throw new Error('MHM could not find smaller steps for this.');
      renderSuggestedSteps(steps);
      if (breakSave) breakSave.hidden = false;
      if (taskStatus) taskStatus.textContent = 'Choose the steps to add. The original task stays.';
    } catch (error) {
      if (taskStatus) {
        taskStatus.textContent = error.message;
        taskStatus.classList.add('is-error');
      }
    } finally {
      setFocusBusy(false);
    }
  });
  if (breakSave) breakSave.addEventListener('click', () => {
    if (!suggestedSteps.length) return undefined;
    return runFocusAction('subtasks', { titles: suggestedSteps }, 'Adding these steps…');
  });
  const stepAdd = document.getElementById('home-task-step-add');
  if (stepAdd) stepAdd.addEventListener('click', () => {
    const field = document.getElementById('home-task-step-title');
    const title = field ? field.value.trim() : '';
    if (!title) return undefined;
    return runFocusAction('subtasks', { titles: [title] }, 'Adding this step…');
  });
  const ownButton = document.getElementById('home-task-own');
  if (ownButton) ownButton.addEventListener('click', () => {
    return runFocusAction('detach', {}, 'Making this its own task…');
  });

  const talkLog = document.getElementById('talk-log');
  const talkForm = document.getElementById('talk-form');
  const talkInput = document.getElementById('talk-input');
  const talkSend = document.getElementById('talk-send');
  const talkStatus = document.getElementById('talk-status');
  const talkSuggestions = document.getElementById('talk-suggestions');
  let speakerName = '';
  let turns = [];
  let historyPages = 1;
  let conversationOpened = false;
  const WINDOW_MS = 48 * 60 * 60 * 1000;
  const MIN_TURNS_PER_PAGE = 6;

  function savedTurns() {
    return turns;
  }

  function applyTurns(saved) {
    turns = (saved || []).filter(turn => turn && (turn.role === 'you' || turn.role === 'mhm') && typeof turn.text === 'string').slice(-80).map(turn => ({
      role: turn.role,
      text: turn.text,
      at: typeof turn.created_at === 'string' ? turn.created_at : '',
      deliveryId: typeof turn.delivery_id === 'string' ? turn.delivery_id : '',
      reaction: turn.reaction === 'up' || turn.reaction === 'down' ? turn.reaction : '',
    }));
  }

  function turnTime(turn) {
    if (!turn.at) return null;
    const parsed = new Date(turn.at.includes('T') ? turn.at : turn.at.replace(' ', 'T'));
    return Number.isNaN(parsed.getTime()) ? null : parsed.getTime();
  }

  function visibleTurns() {
    const saved = savedTurns();
    const cutoff = Date.now() - historyPages * WINDOW_MS;
    const countStart = Math.max(0, saved.length - historyPages * MIN_TURNS_PER_PAGE);
    return saved.filter((turn, index) => {
      const time = turnTime(turn);
      return index >= countStart || time === null || time >= cutoff;
    });
  }

  function hasOlderTurns() {
    return visibleTurns().length < savedTurns().length;
  }

  async function loadConversation() {
    if (talkSend.disabled) return;
    const inbox = await api('/api/chat');
    applyTurns(inbox.turns);
    const nearBottom = !conversationOpened || talkLog.scrollHeight - talkLog.scrollTop - talkLog.clientHeight < 80;
    renderSaved(nearBottom);
    conversationOpened = true;
  }

  function chatStamp(value) {
    if (typeof value !== 'string' || !value.trim()) return '';
    const parsed = new Date(value.includes('T') ? value : value.replace(' ', 'T'));
    if (Number.isNaN(parsed.getTime())) return '';
    return parsed.toLocaleString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' });
  }

  function addBubble(role, text, at, turn) {
    const item = document.createElement('article');
    item.className = role === 'you' ? 'talk-bubble talk-you' : 'talk-bubble talk-mhm';
    const who = document.createElement('span');
    who.textContent = role === 'you' ? (speakerName || 'You') : 'MHM';
    item.append(who);
    const stamp = chatStamp(at);
    if (stamp) {
      const when = document.createElement('time');
      when.dateTime = at.includes('T') ? at : at.replace(' ', 'T');
      when.textContent = stamp;
      item.append(when);
    }
    const body = document.createElement('p');
    body.textContent = text;
    item.append(body);
    if (turn && turn.deliveryId) item.append(reactionChoices(turn));
    talkLog.append(item);
  }

  function reactionChoices(turn) {
    const choices = document.createElement('div');
    choices.className = 'talk-reactions';
    const more = reactionButton('More like this', 'up', turn);
    const less = reactionButton('Not for me', 'down', turn);
    more.addEventListener('click', () => reactToMessage(turn, 'up', more, less));
    less.addEventListener('click', () => reactToMessage(turn, 'down', less, more));
    choices.append(more, less);
    return choices;
  }

  function reactionButton(label, kind, turn) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'plain-button talk-reaction';
    button.textContent = label;
    button.setAttribute('aria-pressed', turn.reaction === kind ? 'true' : 'false');
    return button;
  }

  async function reactToMessage(turn, kind, chosen, other) {
    if (talkSend.disabled) return;
    chosen.disabled = true;
    other.disabled = true;
    talkStatus.classList.remove('is-error');
    try {
      const result = await api('/api/chat/reactions', 'POST', { delivery_id: turn.deliveryId, kind });
      turn.reaction = kind;
      chosen.setAttribute('aria-pressed', 'true');
      other.setAttribute('aria-pressed', 'false');
      talkStatus.textContent = result.reply || '';
    } catch (error) {
      talkStatus.textContent = error.message;
      talkStatus.classList.add('is-error');
    } finally {
      chosen.disabled = false;
      other.disabled = false;
    }
  }

  function pinTalkToLatest() {
    if (!talkLog) return;
    talkLog.scrollTop = talkLog.scrollHeight;
  }

  function showSuggestions(suggestions) {
    talkSuggestions.replaceChildren();
    const usable = (suggestions || []).filter(item => typeof item === 'string' && item.trim());
    talkSuggestions.hidden = usable.length === 0;
    usable.forEach(suggestion => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'plain-button talk-suggestion';
      button.textContent = suggestion;
      button.addEventListener('click', () => sendMessage(suggestion));
      talkSuggestions.append(button);
    });
  }

  function renderSaved(pin) {
    const previousHeight = talkLog.scrollHeight;
    const previousTop = talkLog.scrollTop;
    const hadContent = talkLog.childElementCount > 0;
    talkLog.replaceChildren();
    if (hasOlderTurns()) {
      const more = document.createElement('button');
      more.type = 'button';
      more.className = 'plain-button talk-more';
      more.textContent = 'More';
      more.addEventListener('click', () => {
        historyPages += 1;
        renderSaved(false);
      });
      talkLog.append(more);
    }
    const shown = visibleTurns();
    if (!shown.length && !savedTurns().length) {
      addBubble('mhm', 'Hi. Ask for help, tell me to add a task, or just say what’s on your mind.');
    } else {
      shown.forEach(turn => addBubble(turn.role, turn.text, turn.at, turn));
    }
    const last = shown[shown.length - 1];
    if (last && last.role === 'mhm') showSuggestions(last.suggestions);
    if (pin) pinTalkToLatest();
    else if (hadContent) talkLog.scrollTop = Math.max(0, talkLog.scrollHeight - previousHeight + previousTop);
  }

  async function sendMessage(text) {
    const message = text.trim();
    if (!message || talkSend.disabled) return;
    const sentAt = new Date().toISOString();
    const pendingTurn = { role: 'you', text: message, at: sentAt };
    turns.push(pendingTurn);
    addBubble('you', message, sentAt);
    pinTalkToLatest();
    talkInput.value = '';
    talkSend.disabled = true;
    talkSend.setAttribute('aria-busy', 'true');
    talkSuggestions.hidden = true;
    talkStatus.textContent = 'MHM is replying…';
    talkStatus.classList.remove('is-error');
    try {
      const result = await api('/api/chat', 'POST', { message });
      const reply = result.reply || 'MHM could not answer that just now. Please try again.';
      const repliedAt = new Date().toISOString();
      turns.push({ role: 'mhm', text: reply, at: repliedAt, suggestions: result.suggestions || [] });
      addBubble('mhm', reply, repliedAt);
      pinTalkToLatest();
      showSuggestions(result.suggestions);
      talkStatus.textContent = '';
    } catch (error) {
      const pendingIndex = turns.indexOf(pendingTurn);
      if (pendingIndex >= 0) turns.splice(pendingIndex, 1);
      renderSaved(true);
      talkStatus.textContent = error.message;
      talkStatus.classList.add('is-error');
      if (!talkInput.value.trim()) talkInput.value = message;
      showSuggestions([]);
    } finally {
      talkSend.disabled = false;
      talkSend.removeAttribute('aria-busy');
      talkInput.focus();
    }
  }

  if (talkForm) {
    loadConversation().catch(() => renderSaved());
    window.setInterval(() => {
      loadConversation().catch(() => {});
    }, 20000);
    talkForm.addEventListener('submit', (event) => {
      event.preventDefault();
      sendMessage(talkInput.value);
    });
    talkInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        sendMessage(talkInput.value);
      }
    });
  }


  if (homeContent) loadHome();
})();
