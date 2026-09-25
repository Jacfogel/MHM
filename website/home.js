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

  const PRIORITY_SCORE = { critical: 40, urgent: 32, high: 24, medium: 12, low: 4 };

  function daysUntil(dueDate, now) {
    if (!dueDate || !/^\d{4}-\d{2}-\d{2}$/.test(dueDate)) return null;
    const [year, month, day] = dueDate.split('-').map(Number);
    const due = new Date(year, month - 1, day);
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    return Math.round((due.getTime() - today.getTime()) / 86400000);
  }

  function snoozeUntil(task) {
    const raw = task.reminder_snooze_until;
    if (typeof raw !== 'string' || !raw.trim()) return null;
    const parsed = new Date(raw.includes('T') ? raw : raw.replace(' ', 'T'));
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function timeBand(hour) {
    if (hour < 12) return 'morning';
    if (hour < 17) return 'afternoon';
    if (hour < 21) return 'evening';
    return 'night';
  }

  function scoreFocus(task, now) {
    const until = snoozeUntil(task);
    if (until && until.getTime() > now.getTime()) return null;
    const days = daysUntil(task.due_date, now);
    const priority = String(task.priority || 'medium').toLowerCase();
    const recurring = Boolean(task.recurrence && task.recurrence.pattern);
    const tags = (Array.isArray(task.tags) ? task.tags : []).map(tag => String(tag).toLowerCase());
    const reasons = [];
    let score = PRIORITY_SCORE[priority] || 12;
    if (days === null) score += 5;
    else if (days < 0) {
      score += 80 + Math.min(-days, 14) * 4;
      reasons.push('overdue');
    } else if (days === 0) {
      score += 60;
      reasons.push('due-today');
    } else if (days <= 2) {
      score += 40;
      reasons.push('due-soon');
    } else if (days <= 7) {
      score += 20;
      reasons.push('due-week');
    }
    if (priority === 'critical' || priority === 'urgent' || priority === 'high') reasons.push('priority');
    if (tags.includes(timeBand(now.getHours()))) {
      score += 12;
      reasons.push('time-of-day');
    }
    if (days === 0 && /^\d{2}:\d{2}$/.test(task.due_time || '')) {
      const [hour, minute] = task.due_time.split(':').map(Number);
      const delta = hour * 60 + minute - (now.getHours() * 60 + now.getMinutes());
      if (delta <= 120 && delta >= -180) {
        score += 15;
        reasons.push('due-time');
      }
    }
    if (until) {
      score += 18;
      reasons.push('deferred');
    }
    if (!recurring && days !== null && days <= 0) score += 6;
    else if (recurring) reasons.push('recurring');
    const minutes = Number(task.effort_minutes);
    if (Number.isFinite(minutes) && minutes > 0) {
      reasons.push('effort');
      if (minutes <= 10) score += 22;
      else if (minutes <= 30) score += 10;
      else score -= 8;
    }
    return { task, score: Math.max(score, 1), reasons, days, priority, recurring, minutes: Number.isFinite(minutes) ? minutes : null };
  }

  function chooseFocus(tasks, now = new Date(), random = Math.random) {
    const ranked = (tasks || []).map(task => scoreFocus(task, now)).filter(Boolean);
    if (!ranked.length) return null;
    ranked.sort((left, right) => right.score - left.score || String(left.task.title).localeCompare(String(right.task.title)));
    const roll = typeof random === 'function' ? random() : Math.random();
    const total = ranked.reduce((sum, item) => sum + item.score, 0);
    let cursor = (Number.isFinite(roll) ? roll : 0) * total;
    for (const item of ranked) {
      cursor -= item.score;
      if (cursor < 0) return item;
    }
    return ranked[ranked.length - 1];
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

  function focusReason(pick) {
    const { reasons, priority } = pick;
    if (reasons.includes('deferred') && reasons.includes('overdue')) {
      return 'You already set this aside, and it is still overdue. A small start still counts.';
    }
    if (reasons.includes('overdue')) return 'This is overdue. Clearing it first takes the pressure off.';
    if (reasons.includes('effort') && pick.minutes <= 15 && (reasons.includes('due-today') || reasons.includes('overdue'))) {
      return 'This is probably the easiest useful thing to clear first.';
    }
    if (reasons.includes('due-today') && priority !== 'high' && priority !== 'urgent' && priority !== 'critical') {
      return 'This is probably the easiest useful thing to clear first.';
    }
    if (reasons.includes('due-today')) return 'Due today, and it matters more than the other open tasks.';
    if (reasons.includes('deferred')) return 'You already set this aside once. A small start still counts.';
    if (reasons.includes('due-soon') || reasons.includes('due-week')) {
      return 'This is coming up soon, so starting it now keeps it from becoming urgent.';
    }
    if (reasons.includes('time-of-day')) return 'This fits the time of day better than the other open tasks.';
    return 'No deadline is pressing. This is a calm one to pick up when you have a moment.';
  }

  function noteTitle(text) {
    const line = text.split(/\r?\n/).find(item => item.trim()) || 'Quick note';
    return line.trim().slice(0, 80);
  }

  function accountNeedsSetup(account) {
    return account.needs_setup === true;
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
      const tasks = await api('/api/tasks?status=active');
      let efforts = {};
      try {
        const estimate = await api('/api/tasks/effort');
        efforts = Object.fromEntries((estimate.tasks || []).filter(item => item && item.id).map(item => [item.id, item.minutes]));
      } catch (error) {
        efforts = {};
      }
      const withEffort = (tasks.tasks || []).map(task => ({ ...task, effort_minutes: efforts[task.id] }));
      const pick = chooseFocus(withEffort, new Date(), window.mhmRandom || Math.random);
      focusedTask = pick ? pick.task : null;
      const actions = document.getElementById('home-task-actions');
      const breakForm = document.getElementById('home-task-break-form');
      document.getElementById('home-task-title').textContent = focusedTask ? focusedTask.title : 'No tasks yet.';
      document.getElementById('home-task-meta').textContent = pick
        ? focusMeta(pick)
        : 'Add something small on Tasks, or capture a thought below.';
      document.getElementById('home-task-why').textContent = pick ? focusReason(pick) : '';
      if (actions) actions.hidden = !focusedTask;
      if (breakForm) breakForm.hidden = true;
      const taskStatus = document.getElementById('home-task-status');
      if (taskStatus) {
        taskStatus.textContent = '';
        taskStatus.classList.remove('is-error');
      }
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

  let focusedTask = null;

  function localStamp(now = new Date()) {
    const pad = value => String(value).padStart(2, '0');
    return {
      date: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`,
      time: `${pad(now.getHours())}:${pad(now.getMinutes())}`,
    };
  }

  async function runFocusAction(path, payload, pending) {
    if (!focusedTask) return;
    const taskStatus = document.getElementById('home-task-status');
    const buttons = document.querySelectorAll('#home-task-actions button, #home-task-break-save');
    buttons.forEach(button => { button.disabled = true; });
    if (taskStatus) {
      taskStatus.textContent = pending;
      taskStatus.classList.remove('is-error');
    }
    try {
      await api(`/api/tasks/${encodeURIComponent(focusedTask.id)}/${path}`, 'POST', payload);
      await loadHome();
    } catch (error) {
      if (taskStatus) {
        taskStatus.textContent = error.message;
        taskStatus.classList.add('is-error');
      }
    } finally {
      buttons.forEach(button => { button.disabled = false; });
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
  const breakButton = document.getElementById('home-task-break');
  const breakForm = document.getElementById('home-task-break-form');
  if (breakButton && breakForm) breakButton.addEventListener('click', () => {
    breakForm.hidden = false;
    const smaller = document.getElementById('home-task-smaller');
    if (smaller) smaller.focus();
  });
  if (breakForm) breakForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const smaller = document.getElementById('home-task-smaller');
    const title = smaller ? smaller.value.trim() : '';
    if (!title) return undefined;
    return runFocusAction('simplify', { new_title: title }, 'Saving the smaller step…').then(() => {
      if (smaller) smaller.value = '';
    });
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

  const talkLog = document.getElementById('talk-log');
  const talkForm = document.getElementById('talk-form');
  const talkInput = document.getElementById('talk-input');
  const talkSend = document.getElementById('talk-send');
  const talkStatus = document.getElementById('talk-status');
  const talkSuggestions = document.getElementById('talk-suggestions');
  let speakerName = '';
  let turns = [];
  let historyWindows = 1;
  let conversationOpened = false;
  const WINDOW_MS = 48 * 60 * 60 * 1000;

  function savedTurns() {
    return turns;
  }

  function applyTurns(saved) {
    turns = (saved || []).filter(turn => turn && (turn.role === 'you' || turn.role === 'mhm') && typeof turn.text === 'string').slice(-80).map(turn => ({
      role: turn.role,
      text: turn.text,
      at: typeof turn.created_at === 'string' ? turn.created_at : '',
    }));
  }

  function turnTime(turn) {
    if (!turn.at) return null;
    const parsed = new Date(turn.at.includes('T') ? turn.at : turn.at.replace(' ', 'T'));
    return Number.isNaN(parsed.getTime()) ? null : parsed.getTime();
  }

  function visibleTurns() {
    const cutoff = Date.now() - historyWindows * WINDOW_MS;
    return savedTurns().filter(turn => {
      const time = turnTime(turn);
      return time === null || time >= cutoff;
    });
  }

  function hasOlderTurns() {
    const cutoff = Date.now() - historyWindows * WINDOW_MS;
    return savedTurns().some(turn => {
      const time = turnTime(turn);
      return time !== null && time < cutoff;
    });
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

  function addBubble(role, text, at) {
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
    talkLog.append(item);
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
        historyWindows += 1;
        renderSaved(false);
      });
      talkLog.append(more);
    }
    const shown = visibleTurns();
    if (!shown.length && !savedTurns().length) {
      addBubble('mhm', 'Hi. Ask for help, tell me to add a task, or just say what’s on your mind.');
    } else {
      shown.forEach(turn => addBubble(turn.role, turn.text, turn.at));
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
    turns.push({ role: 'you', text: message, at: sentAt });
    addBubble('you', message, sentAt);
    pinTalkToLatest();
    talkInput.value = '';
    talkSend.disabled = true;
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
      talkStatus.textContent = error.message;
      talkStatus.classList.add('is-error');
      showSuggestions([]);
    } finally {
      talkSend.disabled = false;
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
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage(talkInput.value);
      }
    });
  }


  if (homeContent) loadHome();
})();
