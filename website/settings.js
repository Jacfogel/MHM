(() => {
  const titles = { profile: 'Profile', delivery: 'Delivery', messages: 'Messages', tasks: 'Tasks', checkins: 'Check-ins' };
  const descriptions = {
    profile: 'Tell MHM a little about you. Use one entry per line in each list.',
    delivery: 'Choose where your support arrives and the time zone for your reminders.',
    messages: 'Choose the encouragement you want and when it can reach you.',
    tasks: 'Set reminder windows and the defaults for new recurring tasks.',
    checkins: 'Choose when to check in and which questions to include.',
  };
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const status = document.getElementById('settings-status');
  const retry = document.getElementById('settings-retry');
  const forms = {};
  let saving = false;
  let sessionEnded = false;

  function el(tag, text, props = {}) {
    const node = document.createElement(tag);
    if (text !== null) node.textContent = text;
    for (const [key, value] of Object.entries(props)) {
      if (key === 'className') node.className = value;
      else node.setAttribute(key, value);
    }
    return node;
  }
  function field(parent, title, id, kind, value, props = {}) {
    const wrapper = el('div', null, { className: 'settings-field' });
    const label = el('label', title, { for: id });
    const input = el(kind === 'textarea' ? 'textarea' : 'input', null, { id, ...props });
    if (kind !== 'textarea') input.type = kind;
    if (kind === 'checkbox') input.checked = !!value;
    else input.value = value ?? '';
    if (kind === 'checkbox') { wrapper.classList.add('settings-toggle'); wrapper.append(input, label); }
    else wrapper.append(label, input);
    parent.append(wrapper);
    return input;
  }
  function select(parent, title, id, choices, value) {
    const wrapper = el('div', null, { className: 'settings-field' });
    const input = el('select', null, { id });
    for (const [key, label] of choices) input.append(el('option', label, { value: key }));
    input.value = value ?? '';
    wrapper.append(el('label', title, { for: id }), input);
    parent.append(wrapper);
    return input;
  }
  function lines(input) { return input.value.split('\n').map(line => line.trim()).filter(Boolean); }

  function periodEditor(parent, category, initial) {
    const group = el('fieldset', null, { className: 'period-editor' });
    group.append(el('legend', category.replaceAll('_', ' ') + ' reminder windows'));
    group.append(el('p', 'MHM picks a time within each enabled window. Times use your account’s time zone.', { className: 'field-hint' }));
    const rows = el('div');
    const controls = [];
    function add(name, value) {
      const row = el('div', null, { className: 'period-row' });
      const id = `period-${category}-${crypto.randomUUID()}`;
      const input = field(row, 'Window name', id + '-name', 'text', name, { required: '', maxlength: '80' });
      const times = el('div', null, { className: 'settings-two-col' });
      const start = field(times, 'From', id + '-start', 'time', value.start_time, { required: '' });
      const end = field(times, 'Until', id + '-end', 'time', value.end_time, { required: '' });
      row.append(times);
      const enabled = field(row, 'Enable this window', id + '-active', 'checkbox', value.active);
      const dayGroup = el('fieldset', null, { className: 'day-picker' });
      dayGroup.append(el('legend', 'Days'));
      const dayInputs = days.map(day => [day, field(dayGroup, day.slice(0, 3), id + day, 'checkbox', value.days.includes('ALL') || value.days.includes(day))]);
      row.append(dayGroup);
      const remove = el('button', 'Remove window', { type: 'button', className: 'plain-button' });
      const control = { row, input, start, end, enabled, dayInputs };
      remove.addEventListener('click', () => { controls.splice(controls.indexOf(control), 1); row.remove(); parent.dispatchEvent(new Event('input', { bubbles: true })); });
      row.append(remove);
      controls.push(control);
      rows.append(row);
    }
    for (const [name, value] of Object.entries(initial)) add(name, value);
    const button = el('button', '+ Add reminder window', { type: 'button', className: 'plain-button' });
    button.addEventListener('click', () => {
      if (controls.length >= 20) return;
      add(`Window ${controls.length + 1}`, { start_time: '18:00', end_time: '20:00', active: true, days: ['ALL'] });
      parent.dispatchEvent(new Event('input', { bubbles: true }));
    });
    group.append(rows, button);
    parent.append(group);
    return {
      group,
      read() {
        const result = Object.create(null);
        for (const item of controls) {
          const name = item.input.value.trim();
          if (!name || name.toUpperCase() === 'ALL' || Object.hasOwn(result, name)) throw new Error('Give each reminder window a unique name other than ALL.');
          const selected = item.dayInputs.filter(([, input]) => input.checked).map(([day]) => day);
          result[name] = { active: item.enabled.checked, days: selected.length === 7 ? ['ALL'] : selected, start_time: item.start.value, end_time: item.end.value };
        }
        return result;
      },
    };
  }
  async function api(method, payload) {
    const response = await fetch('/api/settings', {
      method, credentials: 'same-origin', cache: 'no-store',
      ...(payload ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) } : {}),
    });
    if (response.status === 401) {
      window.dispatchEvent(new Event('mhm:signed-out'));
      document.getElementById('account-content').hidden = true;
      location.replace('login.html');
      throw new Error('Please log in again.');
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(data.error || 'MHM could not load your settings. Please try again.');
      error.status = response.status;
      throw error;
    }
    return data;
  }
  function renderSection(section, data) {
    const values = data.sections[section];
    let revision = data.revisions[section];
    const form = el('form', null, { id: `settings-${section}`, className: 'settings-panel', 'aria-labelledby': `title-${section}` });
    form.hidden = section !== 'profile';
    form.append(el('h3', titles[section], { id: `title-${section}` }), el('p', descriptions[section], { className: 'panel-description' }));
    let read;
    if (section === 'profile') {
      const name = field(form, 'Preferred name', 'preferred-name', 'text', values.preferred_name, { maxlength: '100' });
      const fields = {};
      const labels = { pronouns: 'Pronouns', interests: 'Interests', goals: 'Goals', activities_for_encouragement: 'Activities that encourage you', notes_for_ai: 'What you’d like MHM to keep in mind' };
      for (const [key, label] of Object.entries(labels)) fields[key] = field(form, label, key, 'textarea', values[key].join('\n'), { rows: key === 'notes_for_ai' ? '4' : '2' });
      read = () => ({ preferred_name: name.value, ...Object.fromEntries(Object.entries(fields).map(([key, input]) => [key, lines(input)])) });
    } else if (section === 'delivery') {
      const timezone = select(form, 'Time zone', 'timezone', data.options.timezones.map(zone => [zone, zone.replaceAll('_', ' ')]), values.timezone);
      timezone.required = true;
      const channel = select(form, 'Deliver reminders through', 'delivery-channel', [['email', 'Email'], ...(data.discord_linked ? [['discord', 'Discord']] : [])], values.channel);
      form.append(el('p', data.discord_linked ? 'Your verified email and linked Discord account are available for delivery.' : 'Link your account with the MHM Discord bot to enable Discord delivery.', { className: 'field-hint' }));
      read = () => ({ timezone: timezone.value, channel: channel.value });
    } else {
      const enabled = field(form, `Enable ${titles[section].toLowerCase()}`, `enabled-${section}`, 'checkbox', values.enabled);
      if (section === 'messages') {
        const choices = el('fieldset', null, { className: 'category-picker' });
        choices.append(el('legend', 'Message categories'));
        const editors = {};
        const inputs = data.options.categories.map(category => [category, field(choices, category.replaceAll('_', ' '), `category-${category}`, 'checkbox', values.categories.includes(category))]);
        form.append(choices);
        for (const [category, input] of inputs) {
          const editor = periodEditor(form, category, values.periods[category] || data.available_message_periods[category]);
          editors[category] = editor;
          editor.group.hidden = !input.checked;
          editor.group.disabled = !input.checked;
          input.addEventListener('change', () => { editor.group.hidden = !input.checked; editor.group.disabled = !input.checked; });
        }
        read = () => {
          const categories = inputs.filter(([, input]) => input.checked).map(([category]) => category);
          return { enabled: enabled.checked, categories, periods: Object.fromEntries(categories.map(category => [category, editors[category].read()])) };
        };
      } else {
        const periods = periodEditor(form, section === 'tasks' ? 'tasks' : 'checkin', values.periods);
        if (section === 'tasks') {
          const pattern = select(form, 'Default repeat pattern for new tasks', 'recurrence-pattern', [['', 'One-time task'], ['daily', 'Daily'], ['weekly', 'Weekly'], ['monthly', 'Monthly'], ['yearly', 'Yearly']], values.recurring.default_recurrence_pattern);
          const interval = field(form, 'Repeat every (interval)', 'recurrence-interval', 'number', values.recurring.default_recurrence_interval, { min: '1', max: '365', required: '' });
          const after = field(form, 'Count the next repeat from completion', 'repeat-after', 'checkbox', values.recurring.default_repeat_after_completion);
          form.append(el('p', 'These defaults apply to new tasks. Existing tasks keep their own repeat settings.', { className: 'field-hint' }));
          read = () => ({ enabled: enabled.checked, periods: periods.read(), recurring: { default_recurrence_pattern: pattern.value || null, default_recurrence_interval: Number(interval.value), default_repeat_after_completion: after.checked } });
        } else {
          const questions = {};
          for (const [key, label] of Object.entries(data.options.questions)) questions[key] = select(form, label, `question-${key}`, [['off', 'Off'], ['always', 'Always'], ['sometimes', 'Sometimes']], values.questions[key]);
          const counts = el('div', null, { className: 'settings-two-col' });
          const minimum = field(counts, 'Minimum questions', 'min-questions', 'number', values.min_questions, { min: '1', max: '100', required: '' });
          const maximum = field(counts, 'Maximum questions', 'max-questions', 'number', values.max_questions, { min: '1', max: '100', required: '' });
          form.append(counts, el('p', 'Include all Always questions. With Sometimes questions, the maximum must leave at least one out so check-ins can vary.', { className: 'field-hint' }));
          read = () => ({ enabled: enabled.checked, periods: periods.read(), questions: Object.fromEntries(Object.entries(questions).map(([key, input]) => [key, input.value])), min_questions: Number(minimum.value), max_questions: Number(maximum.value) });
        }
      }
    }
    const actions = el('div', null, { className: 'settings-actions' });
    const button = el('button', 'Save changes', { className: 'button', type: 'submit' });
    const feedback = el('p', '', { className: 'form-status', role: 'status', 'aria-live': 'polite' });
    const reload = el('button', 'Reload this section', { className: 'plain-button', type: 'button' });
    reload.hidden = true;
    reload.addEventListener('click', async () => {
      if (saving) return;
      try {
        const latest = await api('GET');
        const replacement = renderSection(section, latest);
        replacement.hidden = false;
        form.replaceWith(replacement);
        forms[section] = replacement;
      } catch (error) { feedback.textContent = error.message; }
    });
    actions.append(button, feedback, reload);
    form.append(actions);
    form.dataset.dirty = 'false';
    form.addEventListener('input', () => { form.dataset.dirty = 'true'; feedback.textContent = 'Unsaved changes'; });
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (saving) return;
      saving = true;
      const controls = Object.values(forms).flatMap(other => [...other.querySelectorAll('input, select, textarea, button')]).map(input => [input, input.disabled]);
      for (const [input] of controls) input.disabled = true;
      feedback.textContent = 'Saving…';
      feedback.classList.remove('is-error');
      try {
        const latest = await api('POST', { section, values: read(), revision });
        revision = latest.revisions[section];
        form.dataset.dirty = 'false';
        feedback.textContent = 'Changes saved';
        if (section === 'delivery') document.getElementById('account-timezone').textContent = latest.sections.delivery.timezone;
        reload.hidden = true;
      } catch (error) {
        feedback.textContent = error.message;
        feedback.classList.add('is-error');
        reload.hidden = true;
        if (error.status === 409 || error.status === 503) reload.hidden = false;
      } finally {
        saving = false;
        for (const [input, disabled] of controls) input.disabled = disabled;
      }
    });
    return form;
  }
  async function load() {
    retry.hidden = true;
    try {
      const data = await api('GET');
      const nav = document.getElementById('settings-nav');
      const panels = document.getElementById('settings-panels');
      nav.replaceChildren(); panels.replaceChildren();
      for (const [section, title] of Object.entries(titles)) {
        const button = el('button', title, { type: 'button', 'aria-controls': `settings-${section}` });
        if (section === 'profile') button.setAttribute('aria-current', 'page');
        button.addEventListener('click', () => {
          for (const [key, form] of Object.entries(forms)) form.hidden = key !== section;
          for (const other of nav.children) other.removeAttribute('aria-current');
          button.setAttribute('aria-current', 'page');
        });
        nav.append(button);
        forms[section] = renderSection(section, data);
        panels.append(forms[section]);
      }
      document.getElementById('settings-layout').hidden = false;
      status.textContent = '';
    } catch (error) { status.textContent = error.message; status.classList.add('is-error'); retry.hidden = false; }
  }
  retry.addEventListener('click', load);
  window.addEventListener('mhm:before-logout', event => {
    if (saving) {
      status.textContent = 'Wait for your settings to finish saving, then log out.';
      event.preventDefault();
      return;
    }
    if (Object.values(forms).some(form => form.dataset.dirty === 'true') && !window.confirm('You have unsaved settings. Log out and discard those changes?')) event.preventDefault();
  });
  window.addEventListener('mhm:signed-out', () => {
    sessionEnded = true;
    for (const form of Object.values(forms)) form.dataset.dirty = 'false';
  });
  window.addEventListener('beforeunload', event => {
    if (!sessionEnded && Object.values(forms).some(form => form.dataset.dirty === 'true')) { event.preventDefault(); event.returnValue = ''; }
  });
  load();
})();
