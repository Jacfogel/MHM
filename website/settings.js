const MHMSettingsInput = Object.freeze({
  profileEntries(value) {
    return String(value ?? '').split(/[\n,;]+/).map(entry => entry.trim()).filter(Boolean);
  },
  record(value) {
    return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  },
  list(value) {
    return Array.isArray(value) ? value : [];
  },
  openPicker(input) {
    if (typeof input.showPicker !== 'function' || input.disabled || input.readOnly) return;
    try { input.showPicker(); } catch (_) { /* The browser's native picker remains available. */ }
  },
  bindPicker(input) {
    input.addEventListener('pointerdown', event => {
      if (typeof event.button === 'number' && event.button !== 0) return;
      MHMSettingsInput.openPicker(input);
    });
  },
});

(() => {
  const titles = { profile: 'Profile', delivery: 'Delivery', phrases: 'Phrases', messages: 'Messages', tasks: 'Tasks', checkins: 'Check-ins' };
  const descriptions = {
    profile: 'Tell MHM a little about you. Separate entries with a new line, comma, or semicolon.',
    delivery: 'Choose where your support arrives and the time zone for your reminders.',
    phrases: 'Choose how MHM interprets everyday time phrases when you create tasks or reminders.',
    messages: 'Choose the encouragement you want and when it can reach you.',
    tasks: 'Set reminder windows and the defaults for new recurring tasks.',
    checkins: 'Choose when to check in and which questions to include.',
  };
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const categoryLabels = {
    personalized_checkin: 'Personalized from check-ins',
    personalized_google_health: 'Personalized from Google Health',
    personalized_profile: 'Personalized from your profile',
  };
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
    if (kind === 'date' || kind === 'time') {
      MHMSettingsInput.bindPicker(input);
    }
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
  function lines(input) { return MHMSettingsInput.profileEntries(input.value); }

  function featureDetails(form, enabled, title) {
    const details = el('fieldset', null, { className: 'settings-feature-details' });
    details.append(el('legend', `${title} details`, { className: 'feature-details-legend' }));
    const update = () => {
      details.disabled = !enabled.checked;
      details.classList.toggle('is-disabled', !enabled.checked);
    };
    enabled.addEventListener('change', update);
    update();
    form.append(details);
    return details;
  }

  function customQuestionEditor(parent, initial, states) {
    initial = MHMSettingsInput.record(initial);
    states = MHMSettingsInput.record(states);
    const group = el('fieldset', null, { className: 'custom-question-editor' });
    group.append(el('legend', 'Custom questions'));
    group.append(el('p', 'Add questions that fit your own routines. Custom questions can use text, yes/no, or a 1–5 scale.', { className: 'field-hint' }));
    const rows = el('div');
    const controls = [];
    function add(key, definition, state = 'off') {
      definition = MHMSettingsInput.record(definition);
      const row = el('div', null, { className: 'custom-question-row' });
      const text = field(row, 'Question', `${key}-text`, 'text', definition.question_text, { required: '', maxlength: '300' });
      const type = select(row, 'Answer type', `${key}-type`, [['optional_text', 'Text'], ['yes_no', 'Yes or no'], ['scale_1_5', '1–5 scale']], definition.type || 'optional_text');
      const frequency = select(row, 'Include', `${key}-frequency`, [['off', 'Off'], ['always', 'Always'], ['sometimes', 'Sometimes']], state);
      const remove = el('button', 'Remove question', { type: 'button', className: 'plain-button danger-button' });
      const control = { key, row, text, type, frequency };
      remove.addEventListener('click', () => {
        controls.splice(controls.indexOf(control), 1);
        row.remove();
        parent.dispatchEvent(new Event('input', { bubbles: true }));
      });
      row.append(remove);
      controls.push(control);
      rows.append(row);
    }
    for (const [key, definition] of Object.entries(initial)) add(key, definition, states[key] || 'sometimes');
    const button = el('button', '+ Add custom question', { type: 'button', className: 'plain-button' });
    button.addEventListener('click', () => {
      if (controls.length >= 20) return;
      const key = `custom_${crypto.randomUUID().replaceAll('-', '')}`;
      add(key, { question_text: '', type: 'optional_text' }, 'off');
      parent.dispatchEvent(new Event('input', { bubbles: true }));
      controls.at(-1).text.focus();
    });
    group.append(rows, button);
    parent.append(group);
    return {
      read() {
        return {
          customQuestions: Object.fromEntries(controls.map(item => [item.key, { question_text: item.text.value.trim(), type: item.type.value }])),
          states: Object.fromEntries(controls.map(item => [item.key, item.frequency.value])),
        };
      },
    };
  }

  function periodEditor(parent, category, initial) {
    initial = MHMSettingsInput.record(initial);
    const group = el('fieldset', null, { className: 'period-editor' });
    group.append(el('legend', category.replaceAll('_', ' ') + ' reminder windows'));
    group.append(el('p', 'MHM picks a time within each enabled window. Times use your account’s time zone.', { className: 'field-hint' }));
    const rows = el('div');
    const controls = [];
    function add(name, value) {
      value = MHMSettingsInput.record(value);
      const selectedDays = MHMSettingsInput.list(value.days);
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
      const dayInputs = days.map(day => [day, field(dayGroup, day.slice(0, 3), id + day, 'checkbox', selectedDays.includes('ALL') || selectedDays.includes(day))]);
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
      const defaults = category === 'tasks'
        ? { start_time: '15:00', end_time: '17:00' }
        : category === 'checkin'
          ? { start_time: '09:30', end_time: '11:30' }
          : { start_time: '18:00', end_time: '20:00' };
      add(`Window ${controls.length + 1}`, { ...defaults, active: true, days: ['ALL'] });
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
  function completeSettingsData(data) {
    const payload = MHMSettingsInput.record(data);
    const sections = MHMSettingsInput.record(payload.sections);
    const revisions = MHMSettingsInput.record(payload.revisions);
    if (Object.keys(titles).some(section => !Object.hasOwn(sections, section))) {
      throw new Error('MHM received incomplete settings data. Please reload your settings.');
    }
    return {
      ...payload,
      sections,
      revisions,
      options: MHMSettingsInput.record(payload.options),
      available_message_periods: MHMSettingsInput.record(payload.available_message_periods),
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
    return completeSettingsData(data);
  }
  function renderSection(section, data) {
    const values = MHMSettingsInput.record(data.sections[section]);
    let revision = data.revisions[section];
    const form = el('form', null, { id: `settings-${section}`, className: 'settings-panel', 'aria-labelledby': `title-${section}` });
    form.hidden = section !== 'profile';
    form.append(el('h3', titles[section], { id: `title-${section}` }), el('p', descriptions[section], { className: 'panel-description' }));
    let read;
    if (section === 'profile') {
      const name = field(form, 'Preferred name', 'preferred-name', 'text', values.preferred_name, { maxlength: '100' });
      const birthDate = field(form, 'Date of birth (optional)', 'date-of-birth', 'date', values.date_of_birth);
      const fields = {};
      const labels = {
        pronouns: 'Pronouns', gender_identity: 'Gender identity', interests: 'Interests', goals: 'Goals',
        activities_for_encouragement: 'Activities that encourage you', health_conditions: 'Health conditions',
        medications_treatments: 'Medications and treatments', allergies_sensitivities: 'Allergies and sensitivities',
        reminders_needed: 'Things you may need reminders for', notes_for_ai: 'What you’d like MHM to keep in mind',
      };
      for (const [key, label] of Object.entries(labels)) fields[key] = field(form, label, key, 'textarea', MHMSettingsInput.list(values[key]).join('\n'), { rows: key === 'notes_for_ai' ? '4' : '2' });
      form.append(el('p', 'Health details are optional and are used only to personalize MHM support.', { className: 'field-hint' }));
      read = () => ({ preferred_name: name.value, date_of_birth: birthDate.value, ...Object.fromEntries(Object.entries(fields).map(([key, input]) => [key, lines(input)])) });
    } else if (section === 'delivery') {
      const timezone = select(form, 'Time zone', 'timezone', MHMSettingsInput.list(data.options.timezones).map(zone => [zone, zone.replaceAll('_', ' ')]), values.timezone);
      timezone.required = true;
      const channel = select(form, 'Deliver reminders through', 'delivery-channel', [['email', 'Email'], ...(data.discord_linked ? [['discord', 'Discord']] : [])], values.channel);
      form.append(el('p', data.discord_linked ? 'Your verified email and linked Discord account are available for delivery.' : 'Link your account with the MHM Discord bot to enable Discord delivery.', { className: 'field-hint' }));
      read = () => ({ timezone: timezone.value, channel: channel.value });
    } else if (section === 'phrases') {
      const first = el('div', null, { className: 'settings-two-col' });
      const tonight = field(first, '“Tonight” starts at', 'phrase-tonight', 'time', values.tonight_start_time, { required: '' });
      const afterWork = field(first, '“After work/school” starts at', 'phrase-after-work', 'time', values.after_work_school_time, { required: '' });
      form.append(first);
      const dayParts = el('div', null, { className: 'settings-two-col' });
      const timeFields = {};
      const timeDefaults = MHMSettingsInput.record(values.time_of_day_defaults);
      for (const key of ['morning', 'afternoon', 'evening', 'night']) {
        timeFields[key] = field(dayParts, `${key[0].toUpperCase()}${key.slice(1)} time`, `phrase-${key}`, 'time', timeDefaults[key], { required: '' });
      }
      form.append(dayParts);
      const weekend = field(form, 'On weekends, “this week” means the coming week', 'phrase-weekend', 'checkbox', values.weekend_this_week_means_coming_week);
      read = () => ({
        tonight_start_time: tonight.value,
        after_work_school_time: afterWork.value,
        time_of_day_defaults: Object.fromEntries(Object.entries(timeFields).map(([key, input]) => [key, input.value])),
        weekend_this_week_means_coming_week: weekend.checked,
      });
    } else {
      const enabled = field(form, `Enable ${titles[section].toLowerCase()}`, `enabled-${section}`, 'checkbox', values.enabled);
      const details = featureDetails(form, enabled, titles[section]);
      if (section === 'messages') {
        const selectedCategories = MHMSettingsInput.list(values.categories);
        const messagePeriods = MHMSettingsInput.record(values.periods);
        const choices = el('fieldset', null, { className: 'category-picker' });
        choices.append(el('legend', 'Message categories'));
        const editors = {};
        const inputs = MHMSettingsInput.list(data.options.categories).map(category => [category, field(choices, categoryLabels[category] || category.replaceAll('_', ' '), `category-${category}`, 'checkbox', selectedCategories.includes(category))]);
        details.append(choices);
        for (const [category, input] of inputs) {
          const editor = periodEditor(details, category, messagePeriods[category] || data.available_message_periods[category]);
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
        const periods = periodEditor(details, section === 'tasks' ? 'tasks' : 'checkin', values.periods);
        if (section === 'tasks') {
          const recurring = MHMSettingsInput.record(values.recurring);
          const pattern = select(details, 'Default repeat pattern for new tasks', 'recurrence-pattern', [['', 'One-time task'], ['daily', 'Daily'], ['weekly', 'Weekly'], ['monthly', 'Monthly'], ['yearly', 'Yearly']], recurring.default_recurrence_pattern);
          const interval = field(details, 'Repeat every (interval)', 'recurrence-interval', 'number', recurring.default_recurrence_interval ?? 1, { min: '1', max: '365', required: '' });
          const after = field(details, 'Count the next repeat from completion', 'repeat-after', 'checkbox', recurring.default_repeat_after_completion);
          details.append(el('p', 'These defaults apply to new tasks. Existing tasks keep their own repeat settings.', { className: 'field-hint' }));
          read = () => ({ enabled: enabled.checked, periods: periods.read(), recurring: { default_recurrence_pattern: pattern.value || null, default_recurrence_interval: Number(interval.value), default_repeat_after_completion: after.checked } });
        } else {
          const standardQuestions = MHMSettingsInput.record(data.options.questions);
          const customQuestions = MHMSettingsInput.record(values.custom_questions);
          const questionStates = MHMSettingsInput.record(values.questions);
          const questions = {};
          for (const [key, label] of Object.entries(standardQuestions)) {
            if (!Object.hasOwn(customQuestions, key)) questions[key] = select(details, label, `question-${key}`, [['off', 'Off'], ['always', 'Always'], ['sometimes', 'Sometimes']], questionStates[key]);
          }
          const custom = customQuestionEditor(details, customQuestions, questionStates);
          const counts = el('div', null, { className: 'settings-two-col' });
          const minimum = field(counts, 'Minimum questions', 'min-questions', 'number', values.min_questions, { min: '1', max: '100', required: '' });
          const maximum = field(counts, 'Maximum questions', 'max-questions', 'number', values.max_questions, { min: '1', max: '100', required: '' });
          details.append(counts, el('p', 'Include all Always questions. With Sometimes questions, the maximum must leave at least one out so check-ins can vary.', { className: 'field-hint' }));
          read = () => {
            const customValues = custom.read();
            return { enabled: enabled.checked, periods: periods.read(), questions: { ...Object.fromEntries(Object.entries(questions).map(([key, input]) => [key, input.value])), ...customValues.states }, custom_questions: customValues.customQuestions, min_questions: Number(minimum.value), max_questions: Number(maximum.value) };
          };
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
        if (section === 'checkins' && forms.messages?.dataset.dirty === 'false') {
          const currentMessages = forms.messages;
          const replacement = renderSection('messages', latest);
          replacement.hidden = currentMessages.hidden;
          currentMessages.replaceWith(replacement);
          forms.messages = replacement;
        }
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
