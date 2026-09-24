(() => {
  const status = document.getElementById('checkin-status');
  const panel = document.getElementById('checkin-panel');
  const progress = document.getElementById('checkin-progress');
  const message = document.getElementById('checkin-message');
  const off = document.getElementById('checkin-off');
  const start = document.getElementById('checkin-start');
  const form = document.getElementById('checkin-form');
  const choices = document.getElementById('checkin-choices');
  const sleepPanel = document.getElementById('checkin-sleep');
  const sleepChunks = document.getElementById('checkin-sleep-chunks');
  const sleepAdd = document.getElementById('checkin-sleep-add');
  const answerField = document.getElementById('checkin-answer-field');
  const answer = document.getElementById('checkin-answer');
  const save = document.getElementById('checkin-save');

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
    answer.value = '';
    renderChoices(result);
    showStatus('');
  }

  function choiceButton(label, value) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'button button-small';
    button.textContent = label;
    button.addEventListener('click', () => send({ action: 'answer', answer: value }));
    return button;
  }

  function timeSelect(values, selected) {
    const select = document.createElement('select');
    for (const value of values) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      option.selected = value === selected;
      select.appendChild(option);
    }
    return select;
  }

  function sleepTime(label, hour, minute, meridiem) {
    const field = document.createElement('label');
    field.textContent = label;
    const times = document.createElement('span');
    times.className = 'checkin-sleep-times';
    times.append(
      timeSelect(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'], hour),
      timeSelect(['00', '15', '30', '45'], minute),
      timeSelect(['AM', 'PM'], meridiem),
    );
    field.appendChild(times);
    return field;
  }

  function sleepRow(removable) {
    const row = document.createElement('div');
    row.className = 'checkin-sleep-row';
    row.append(sleepTime('Fell asleep', '11', '00', 'PM'), sleepTime('Woke up', '7', '00', 'AM'));
    if (removable) {
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'plain-button';
      remove.textContent = 'Remove';
      remove.addEventListener('click', () => {
        row.remove();
        refreshSleepAdd();
      });
      row.appendChild(remove);
    }
    return row;
  }

  function refreshSleepAdd() {
    sleepAdd.hidden = sleepChunks.childElementCount >= 3;
  }

  function renderSleep() {
    sleepChunks.replaceChildren(sleepRow(false));
    refreshSleepAdd();
  }

  function sleepAnswer() {
    return [...sleepChunks.querySelectorAll('.checkin-sleep-row')].map(row => {
      const [hour, minute, meridiem, wakeHour, wakeMinute, wakeMeridiem] = [...row.querySelectorAll('select')].map(select => select.value);
      return `${hour}:${minute} ${meridiem}-${wakeHour}:${wakeMinute} ${wakeMeridiem}`;
    }).join('; ');
  }

  function renderChoices(result) {
    choices.replaceChildren();
    const type = result.active ? result.question_type : null;
    const sleep = type === 'time_pair';
    const typed = type !== 'scale_1_5' && type !== 'yes_no' && !sleep;
    if (type === 'scale_1_5') {
      for (let number = 1; number <= 5; number += 1) choices.appendChild(choiceButton(String(number), String(number)));
    } else if (type === 'yes_no') {
      choices.appendChild(choiceButton('Yes', 'yes'));
      choices.appendChild(choiceButton('No', 'no'));
    }
    if (type === 'optional_text') answer.placeholder = 'A short note';
    else answer.placeholder = 'A number, yes or no, or a short note';
    if (sleep) renderSleep();
    sleepPanel.hidden = !sleep;
    answerField.hidden = !typed;
    save.hidden = type === 'scale_1_5' || type === 'yes_no';
    answer.required = typed;
    choices.hidden = choices.childElementCount === 0;
  }

  async function send(payload) {
    showStatus(payload.action === 'start' ? 'Starting your check-in…' : 'Saving…');
    try {
      show(await api('/api/checkins', 'POST', payload));
      if (!form.hidden && !answerField.hidden) answer.focus();
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  start.addEventListener('click', () => send({ action: 'start' }));
  form.addEventListener('submit', event => {
    event.preventDefault();
    send({ action: 'answer', answer: sleepPanel.hidden ? answer.value.trim() : sleepAnswer() });
  });
  sleepAdd.addEventListener('click', () => {
    if (sleepChunks.childElementCount >= 3) return;
    sleepChunks.appendChild(sleepRow(true));
    refreshSleepAdd();
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
