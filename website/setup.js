(() => {
  const status = document.getElementById('setup-status');
  const setupContent = document.getElementById('setup-content');
  const continueButton = document.getElementById('setup-continue');
  const skipButton = document.getElementById('setup-skip');
  const backButton = document.getElementById('setup-back');
  const setupForm = document.getElementById('setup-form');
  const progress = document.getElementById('setup-progress');
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const categoryLabels = {
    personalized_checkin: 'Personalized from check-ins',
    personalized_google_health: 'Personalized from Google Health',
    personalized_profile: 'Personalized from your profile',
  };
  const steps = {
    you: { label: 'You', panel: 'step-1', skip: false },
    discord: { label: 'Discord', panel: 'step-discord', skip: false },
    features: { label: 'Features', panel: 'step-2', skip: false },
    'message-categories': { label: 'Categories', panel: 'step-message-categories', skip: false },
    'message-windows': { label: 'Message times', panel: 'step-message-windows', skip: true },
    'task-create': { label: 'A task', panel: 'step-task-create', skip: true },
    'task-windows': { label: 'Task times', panel: 'step-task-windows', skip: true },
    'checkin-questions': { label: 'Questions', panel: 'step-checkin-questions', skip: false },
    'checkin-windows': { label: 'Check-in times', panel: 'step-checkin-windows', skip: true },
  };
  let settings;
  let account;
  let plan = ['you', 'discord', 'features'];
  let index = 0;

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

  function el(tag, text, props = {}) {
    const node = document.createElement(tag);
    if (text !== null) node.textContent = text;
    for (const [key, value] of Object.entries(props)) {
      if (key === 'className') node.className = value;
      else node.setAttribute(key, value);
    }
    return node;
  }

  function defaultWindow(start, end) {
    return { 'Window 1': { active: true, days: ['ALL'], start_time: start, end_time: end } };
  }

  function withWindow(periods, start, end) {
    return periods && Object.keys(periods).length ? periods : defaultWindow(start, end);
  }

  function selectedSupport() {
    return {
      messages: document.getElementById('enable-messages').checked,
      tasks: document.getElementById('enable-tasks').checked,
      checkins: document.getElementById('enable-checkins').checked,
    };
  }

  function buildPlan() {
    const chosen = selectedSupport();
    const next = ['you', 'discord', 'features'];
    if (chosen.messages) next.push('message-categories', 'message-windows');
    if (chosen.tasks) next.push('task-create', 'task-windows');
    if (chosen.checkins) next.push('checkin-questions', 'checkin-windows');
    plan = next;
  }

  function renderProgress() {
    const current = plan[index];
    progress.replaceChildren();
    for (const id of plan) {
      const item = el('li', steps[id].label);
      item.classList.toggle('is-current', id === current);
      if (id === current) item.setAttribute('aria-current', 'step');
      progress.append(item);
    }
  }

  function bindTime(input) {
    input.addEventListener('pointerdown', event => {
      if (typeof event.button === 'number' && event.button !== 0) return;
      if (typeof input.showPicker !== 'function' || input.disabled) return;
      try { input.showPicker(); } catch (_) { /* The browser's native picker remains available. */ }
    });
  }

  function textField(parent, labelText, value, props = {}) {
    const wrap = el('div', null, { className: 'settings-field' });
    const input = el('input', null, props);
    input.id = props.id || `setup-${crypto.randomUUID()}`;
    input.value = value ?? '';
    wrap.append(el('label', labelText, { for: input.id }), input);
    parent.append(wrap);
    if (input.type === 'time') bindTime(input);
    return input;
  }

  function checkboxField(parent, labelText, checked) {
    const wrap = el('div', null, { className: 'settings-field settings-toggle' });
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.id = `setup-${crypto.randomUUID()}`;
    input.checked = Boolean(checked);
    wrap.append(input, el('label', labelText, { for: input.id }));
    parent.append(wrap);
    return input;
  }

  function periodEditor(parent, category, initial, defaults) {
    const group = el('fieldset', null, { className: 'period-editor' });
    group.append(el('legend', `${category.replaceAll('_', ' ')} reminder windows`));
    group.append(el('p', 'MHM picks a time within each enabled window. Times use your account’s time zone.', { className: 'field-hint' }));
    const rows = el('div');
    const controls = [];
    const deleted = [];
    const undo = el('button', 'Undo last window deletion', { type: 'button', className: 'plain-button' });
    undo.hidden = true;

    function add(name, value) {
      const selectedDays = Array.isArray(value.days) ? value.days : ['ALL'];
      const row = el('div', null, { className: 'period-row' });
      const input = textField(row, 'Window name', name, { type: 'text', required: '', maxlength: '80' });
      const times = el('div', null, { className: 'settings-two-col' });
      const start = textField(times, 'From', value.start_time, { type: 'time', required: '' });
      const end = textField(times, 'Until', value.end_time, { type: 'time', required: '' });
      row.append(times);
      const enabled = checkboxField(row, 'Enable this window', value.active !== false);
      const dayGroup = el('fieldset', null, { className: 'day-picker' });
      dayGroup.append(el('legend', 'Days'));
      const dayInputs = days.map(day => [day, checkboxField(dayGroup, day.slice(0, 3), selectedDays.includes('ALL') || selectedDays.includes(day))]);
      row.append(dayGroup);
      const remove = el('button', 'Remove window', { type: 'button', className: 'plain-button' });
      const control = { row, input, start, end, enabled, dayInputs };
      remove.addEventListener('click', () => {
        deleted.push({
          name: control.input.value,
          value: {
            active: control.enabled.checked,
            days: control.dayInputs.filter(([, box]) => box.checked).map(([day]) => day),
            start_time: control.start.value,
            end_time: control.end.value,
          },
        });
        controls.splice(controls.indexOf(control), 1);
        row.remove();
        undo.hidden = false;
      });
      row.append(remove);
      controls.push(control);
      rows.append(row);
    }

    for (const [name, value] of Object.entries(initial || {})) add(name, value);
    const button = el('button', '+ Add reminder window', { type: 'button', className: 'plain-button' });
    button.addEventListener('click', () => {
      if (controls.length >= 20) return;
      add(`Window ${controls.length + 1}`, { ...defaults, active: true, days: ['ALL'] });
    });
    undo.addEventListener('click', () => {
      const item = deleted.pop();
      if (!item || controls.length >= 20) return;
      add(item.name, item.value);
      undo.hidden = deleted.length === 0;
    });
    group.append(rows, button, undo);
    parent.append(group);
    return {
      read() {
        const result = {};
        for (const item of controls) {
          const name = item.input.value.trim();
          if (!name || name.toUpperCase() === 'ALL' || Object.hasOwn(result, name)) {
            throw new Error('Give each reminder window a unique name other than ALL.');
          }
          const selected = item.dayInputs.filter(([, box]) => box.checked).map(([day]) => day);
          if (item.enabled.checked && !selected.length) {
            throw new Error('Choose at least one day for each enabled reminder window.');
          }
          result[name] = {
            active: item.enabled.checked,
            days: selected.length === 7 ? ['ALL'] : selected,
            start_time: item.start.value,
            end_time: item.end.value,
          };
        }
        if (!Object.values(result).some(window => window.active)) {
          throw new Error('Add at least one enabled reminder window.');
        }
        return result;
      },
    };
  }

  function renderMessageCategories() {
    const root = document.getElementById('message-categories');
    root.replaceChildren();
    const available = settings.options.categories || [];
    const selected = new Set(settings.sections.messages.categories || []);
    if (!selected.size) {
      if (available.includes('motivational')) selected.add('motivational');
      else if (available[0]) selected.add(available[0]);
    }
    for (const category of available) {
      const label = el('label', null, { className: 'setup-choice' });
      const input = el('input', null, { type: 'checkbox', value: category });
      input.checked = selected.has(category);
      const text = el('span');
      text.append(el('strong', categoryLabels[category] || category.replaceAll('_', ' ')));
      label.append(input, text);
      root.append(label);
    }
  }

  function renderMessageWindows() {
    const root = document.getElementById('message-windows');
    root.replaceChildren();
    const categories = settings.sections.messages.categories || [];
    root.editors = categories.map(category => periodEditor(
      root,
      category,
      withWindow(
        (settings.sections.messages.periods || {})[category] || (settings.available_message_periods || {})[category],
        '18:00',
        '20:00',
      ),
      { start_time: '18:00', end_time: '20:00' },
    ));
  }

  function renderTaskWindows() {
    const root = document.getElementById('task-windows');
    root.replaceChildren();
    root.editor = periodEditor(
      root,
      'tasks',
      withWindow(settings.sections.tasks.periods, '15:00', '17:00'),
      { start_time: '15:00', end_time: '17:00' },
    );
  }

  function questionGroups() {
    const questions = settings.options.questions || {};
    const custom = settings.sections.checkins.custom_questions || {};
    const categoryMap = settings.options.question_category_map || {};
    const categories = settings.options.question_categories || {};
    const groups = new Map();
    for (const [key, value] of Object.entries(categories)) {
      if (!value || typeof value !== 'object') continue;
      groups.set(key, {
        name: value.name || key.replaceAll('_', ' '),
        description: value.description || '',
        questions: [],
      });
    }
    for (const [key, label] of Object.entries(questions)) {
      if (Object.hasOwn(custom, key)) continue;
      const category = categoryMap[key] || 'general';
      if (!groups.has(category)) {
        groups.set(category, {
          name: category === 'general' ? 'General' : category.replaceAll('_', ' '),
          description: '',
          questions: [],
        });
      }
      groups.get(category).questions.push({ key, label: String(label) });
    }
    return [...groups.values()].filter(group => group.questions.length);
  }

  function renderCheckinQuestions() {
    const root = document.getElementById('checkin-questions');
    root.replaceChildren();
    const states = settings.sections.checkins.questions || {};
    const defaults = settings.options.question_defaults || {};
    const layout = el('div', null, { className: 'checkin-question-groups' });
    for (const group of questionGroups()) {
      const fieldset = el('fieldset', null, { className: 'checkin-question-group' });
      fieldset.append(el('legend', group.name));
      if (group.description) fieldset.append(el('p', group.description, { className: 'field-hint' }));
      for (const question of group.questions) {
        const row = el('div', null, { className: 'checkin-question-row' });
        const select = document.createElement('select');
        select.id = `question-${question.key}`;
        select.dataset.question = question.key;
        for (const [value, label] of [['off', 'Off'], ['sometimes', 'Sometimes'], ['always', 'Always']]) {
          select.append(el('option', label, { value }));
        }
        select.value = states[question.key] || defaults[question.key] || 'off';
        row.append(el('label', question.label, { for: select.id }), select);
        fieldset.append(row);
      }
      layout.append(fieldset);
    }
    root.append(layout);
  }

  function renderCheckinWindows() {
    const root = document.getElementById('checkin-windows');
    root.replaceChildren();
    root.editor = periodEditor(
      root,
      'checkin',
      withWindow(settings.sections.checkins.periods, '09:30', '11:30'),
      { start_time: '09:30', end_time: '11:30' },
    );
  }

  function setPanelEnabled(panel, enabled) {
    for (const control of panel.querySelectorAll('input, select, textarea, button')) {
      if (control.dataset.unavailable === 'true') {
        control.disabled = true;
        continue;
      }
      control.disabled = !enabled;
    }
  }

  function showCurrent() {
    if (plan[index] === 'features') buildPlan();
    for (const step of Object.values(steps)) {
      const panel = document.getElementById(step.panel);
      panel.hidden = true;
      setPanelEnabled(panel, false);
    }
    const current = steps[plan[index]];
    const panel = document.getElementById(current.panel);
    panel.hidden = false;
    setPanelEnabled(panel, true);
    renderProgress();
    if (plan[index] === 'message-categories') renderMessageCategories();
    if (plan[index] === 'message-windows') renderMessageWindows();
    if (plan[index] === 'task-windows') renderTaskWindows();
    if (plan[index] === 'checkin-questions') renderCheckinQuestions();
    if (plan[index] === 'checkin-windows') renderCheckinWindows();
    const discordLinked = Boolean(account && account.discord_linked);
    const discordAvailable = Boolean(account && account.discord_available);
    const connectDiscord = document.getElementById('setup-connect-discord');
    const discordState = document.getElementById('discord-setup-state');
    if (plan[index] === 'discord') {
      connectDiscord.hidden = discordLinked || !discordAvailable;
      discordState.textContent = discordLinked
        ? 'Discord is connected. MHM can send reminders there. You can switch to email later in Account.'
        : discordAvailable
          ? 'Discord is not connected yet.'
          : 'Discord connection is not available right now, so email will be used.';
    }
    continueButton.textContent = plan[index] === 'discord' && !discordLinked
      ? 'Use email instead'
      : index === plan.length - 1 ? 'Finish →' : 'Continue →';
    skipButton.hidden = !current.skip;
    skipButton.textContent = plan[index].endsWith('windows') ? 'Keep these windows' : 'Skip this step';
    backButton.hidden = index === 0;
  }

  async function advance() {
    if (index >= plan.length - 1) {
      await api('/api/account/setup-complete', 'POST', {});
      location.assign('home.html');
      return;
    }
    index += 1;
    showStatus('');
    showCurrent();
  }

  async function saveSection(section, values) {
    settings = await api('/api/settings', 'POST', {
      section,
      revision: settings.revisions[section],
      values,
    });
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

  async function saveDeliveryChannel(channel) {
    await saveSection('delivery', { ...settings.sections.delivery, channel });
  }

  async function saveDiscordChoice() {
    await saveDeliveryChannel(account && account.discord_linked ? 'discord' : 'email');
  }

  async function saveYou() {
    const name = document.getElementById('preferred-name').value.trim();
    const timezone = document.getElementById('timezone').value;
    await saveSection('profile', { ...settings.sections.profile, preferred_name: name });
    await saveSection('delivery', { ...settings.sections.delivery, timezone });
  }

  async function saveFeatures() {
    const chosen = selectedSupport();
    if (chosen.messages && !(settings.options.categories || []).length) {
      throw new Error('Message categories are not available yet. Uncheck supportive messages, or turn them on later in Account.');
    }
    if (!chosen.messages) await saveSection('messages', { ...settings.sections.messages, enabled: false });
    if (!chosen.tasks) await saveSection('tasks', taskValues(false));
    if (!chosen.checkins) await saveSection('checkins', checkinValues(false));
    buildPlan();
  }

  async function saveMessageCategories() {
    const categories = [...document.querySelectorAll('#message-categories input:checked')].map(input => input.value);
    if (!categories.length) throw new Error('Pick at least one message category.');
    const periods = {};
    for (const category of categories) {
      periods[category] = withWindow(
        (settings.sections.messages.periods || {})[category] || (settings.available_message_periods || {})[category],
        '18:00',
        '20:00',
      );
    }
    await saveSection('messages', { ...settings.sections.messages, enabled: true, categories, periods });
  }

  async function saveMessageWindows() {
    const categories = settings.sections.messages.categories || [];
    const editors = document.getElementById('message-windows').editors || [];
    const periods = {};
    categories.forEach((category, position) => {
      periods[category] = editors[position].read();
    });
    await saveSection('messages', { ...settings.sections.messages, enabled: true, categories, periods });
  }

  async function saveTaskFeature() {
    await saveSection('tasks', taskValues(true));
  }

  async function saveFirstTask() {
    await saveTaskFeature();
    const title = document.getElementById('first-task').value.trim();
    if (!title) return;
    await api('/api/tasks', 'POST', { title });
    document.getElementById('first-task').value = '';
  }

  async function saveTaskWindows() {
    const periods = document.getElementById('task-windows').editor.read();
    await saveSection('tasks', { ...settings.sections.tasks, enabled: true, periods });
  }

  function questionStates() {
    const saved = settings.sections.checkins.questions || {};
    const custom = settings.sections.checkins.custom_questions || {};
    const defaults = settings.options.question_defaults || {};
    const states = {};
    for (const key of Object.keys(settings.options.questions || {})) {
      if (Object.hasOwn(custom, key)) continue;
      states[key] = saved[key] || defaults[key] || 'off';
    }
    for (const key of Object.keys(custom)) states[key] = saved[key] || 'sometimes';
    for (const select of document.querySelectorAll('#checkin-questions select')) {
      if (Object.hasOwn(states, select.dataset.question)) states[select.dataset.question] = select.value;
    }
    return states;
  }

  function fitQuestionCounts(states) {
    const values = Object.values(states);
    const always = values.filter(state => state === 'always').length;
    const sometimes = values.filter(state => state === 'sometimes').length;
    const total = always + sometimes;
    if (!total) throw new Error('Choose at least one check-in question.');
    const floor = Math.max(always, 1);
    const cap = sometimes ? total - 1 : total;
    if (floor > cap) {
      throw new Error('Leave at least one Sometimes question out, or change an Always question to Sometimes.');
    }
    const current = settings.sections.checkins;
    let minimum = Number.isInteger(current.min_questions) ? current.min_questions : floor;
    let maximum = Number.isInteger(current.max_questions) ? current.max_questions : total;
    if (minimum < floor) minimum = floor;
    if (minimum > cap) minimum = cap;
    const lowestMaximum = Math.max(always + (sometimes ? 1 : 0), 1);
    if (maximum < lowestMaximum) maximum = lowestMaximum;
    if (maximum > total) maximum = total;
    if (maximum < minimum) maximum = minimum;
    return { minimum, maximum };
  }

  async function saveCheckinQuestions() {
    const questions = questionStates();
    const counts = fitQuestionCounts(questions);
    await saveSection('checkins', {
      ...checkinValues(true),
      questions,
      min_questions: counts.minimum,
      max_questions: counts.maximum,
    });
  }

  async function saveCheckinWindows() {
    const periods = document.getElementById('checkin-windows').editor.read();
    await saveSection('checkins', { ...settings.sections.checkins, enabled: true, periods });
  }

  const actions = {
    you: saveYou,
    discord: saveDiscordChoice,
    features: saveFeatures,
    'message-categories': saveMessageCategories,
    'message-windows': saveMessageWindows,
    'task-create': saveFirstTask,
    'task-windows': saveTaskWindows,
    'checkin-questions': saveCheckinQuestions,
    'checkin-windows': saveCheckinWindows,
  };

  function accountNeedsSetup(account, currentSettings) {
    if (account.needs_setup === true) return true;
    const flags = ['messages_enabled', 'tasks_enabled', 'checkins_enabled'];
    const known = flags.filter(key => typeof account[key] === 'boolean');
    if (known.some(key => account[key])) return false;
    if (known.length === flags.length) return true;
    const sections = currentSettings.sections || {};
    return ['messages', 'tasks', 'checkins'].every(key => sections[key] && sections[key].enabled === false);
  }

  function setBusy(busy) {
    continueButton.disabled = busy;
    skipButton.disabled = busy;
    backButton.disabled = busy;
    if (busy) continueButton.setAttribute('aria-busy', 'true');
    else continueButton.removeAttribute('aria-busy');
  }

  async function loadSetup() {
    if (!setupContent) return;
    try {
      account = await api('/api/account');
      settings = await api('/api/settings');
      if (!accountNeedsSetup(account, settings)) {
        location.assign('home.html');
        return;
      }
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
      const messagesToggle = document.getElementById('enable-messages');
      if (canMessage) delete messagesToggle.dataset.unavailable;
      else messagesToggle.dataset.unavailable = 'true';
      messagesToggle.disabled = !canMessage;
      messagesToggle.checked = canMessage;
      const discordResult = new URLSearchParams(location.search).get('discord');
      if (discordResult) {
        index = plan.indexOf('discord');
        if (discordResult === 'connected' && account.discord_linked) {
          await saveDeliveryChannel('discord');
        }
        history.replaceState(null, '', location.pathname);
      }
      setupContent.hidden = false;
      showCurrent();
      if (discordResult === 'connected' && account.discord_linked) {
        showStatus('Discord is connected.');
      } else if (discordResult === 'cancelled') {
        showStatus('Discord connection was canceled. You can try again, or use email.');
      } else if (discordResult === 'in-use') {
        showStatus('That Discord account is already connected to another MHM account.', true);
      } else if (discordResult === 'account-linked') {
        showStatus('This MHM account already has a different Discord account connected.', true);
      } else if (discordResult === 'unavailable') {
        showStatus('Discord connection is not configured right now.', true);
      } else if (discordResult === 'error') {
        showStatus('Discord could not be connected. Please try again.', true);
      }
    } catch (error) {
      showStatus(error.message, true);
    }
  }

  if (setupForm) setupForm.addEventListener('submit', async event => {
    event.preventDefault();
    if (continueButton.disabled) return;
    setBusy(true);
    showStatus(index === plan.length - 1 ? 'Finishing…' : 'Saving…');
    try {
      await actions[plan[index]]();
      await advance();
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setBusy(false);
    }
  });

  if (skipButton) skipButton.addEventListener('click', async () => {
    if (skipButton.disabled) return;
    setBusy(true);
    try {
      if (plan[index] === 'task-create') {
        showStatus('Saving…');
        await saveTaskFeature();
      }
      await advance();
    } catch (error) {
      showStatus(error.message, true);
    } finally {
      setBusy(false);
    }
  });

  if (backButton) backButton.addEventListener('click', () => {
    if (backButton.disabled || index === 0) return;
    index -= 1;
    showStatus('');
    showCurrent();
  });

  const connectDiscord = document.getElementById('setup-connect-discord');
  if (connectDiscord) connectDiscord.addEventListener('click', async () => {
    if (connectDiscord.disabled) return;
    connectDiscord.disabled = true;
    showStatus('Opening Discord…');
    try {
      const result = await api('/api/auth/discord/start?next=/setup.html');
      if (!result.url) throw new Error('Discord connection is unavailable.');
      location.assign(result.url);
    } catch (error) {
      showStatus(error.message, true);
      connectDiscord.disabled = false;
    }
  });

  for (const id of ['enable-messages', 'enable-tasks', 'enable-checkins']) {
    document.getElementById(id).addEventListener('change', () => {
      if (plan[index] !== 'features') return;
      buildPlan();
      renderProgress();
    });
  }

  if (setupContent) loadSetup();
})();
