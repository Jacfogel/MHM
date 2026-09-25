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
      const task = nextTask(tasks.tasks || []);
      document.getElementById('home-task-title').textContent = task ? task.title : 'No tasks yet.';
      document.getElementById('home-task-meta').textContent = task
        ? dueLabel(task)
        : 'Add something small on Tasks, or capture a thought below.';
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

  async function loadConversation() {
    if (talkSend.disabled) return;
    const inbox = await api('/api/chat');
    applyTurns(inbox.turns);
    renderSaved();
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
    pinTalkToLatest();
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

  function renderSaved() {
    talkLog.replaceChildren();
    const turns = savedTurns();
    if (!turns.length) {
      addBubble('mhm', 'Hi. Ask for help, tell me to add a task, or just say what’s on your mind.');
      return;
    }
    turns.forEach(turn => addBubble(turn.role, turn.text, turn.at));
    const last = turns[turns.length - 1];
    if (last && last.role === 'mhm') showSuggestions(last.suggestions);
  }

  async function sendMessage(text) {
    const message = text.trim();
    if (!message || talkSend.disabled) return;
    const sentAt = new Date().toISOString();
    turns.push({ role: 'you', text: message, at: sentAt });
    addBubble('you', message, sentAt);
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
