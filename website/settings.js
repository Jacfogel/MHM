const MHMSettingsInput = Object.freeze({
  profileEntries(value) {
    if (typeof value !== 'string') throw new TypeError('Profile entries must be text.');
    return value.split(/[\n,;]+/).map(entry => entry.trim()).filter(Boolean);
  },
  record(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new TypeError('Settings data must use the current object format.');
    return value;
  },
  list(value) {
    if (!Array.isArray(value)) throw new TypeError('Settings data must use the current list format.');
    return value;
  },
  questionGroups(questions, customQuestions, categoryMap, categories) {
    const groups = new Map();
    for (const [key, value] of Object.entries(MHMSettingsInput.record(categories))) {
      const metadata = MHMSettingsInput.record(value);
      groups.set(key, { key, name: metadata.name || key.replaceAll('_', ' '), description: metadata.description || '', questions: [] });
    }
    for (const [key, label] of Object.entries(MHMSettingsInput.record(questions))) {
      if (Object.hasOwn(MHMSettingsInput.record(customQuestions), key)) continue;
      const category = MHMSettingsInput.record(categoryMap)[key] || 'general';
      if (!groups.has(category)) groups.set(category, { key: category, name: category === 'general' ? 'General' : category.replaceAll('_', ' '), description: '', questions: [] });
      groups.get(category).questions.push({ key, label });
    }
    return [...groups.values()].filter(group => group.questions.length);
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
  scrollToSection(section, reducedMotion = false) {
    if (!section || typeof section.scrollIntoView !== 'function') return;
    section.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'start' });
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

  function lovedOnesEditor(parent, initial) {
    const group = el('fieldset', null, { className: 'custom-question-editor' });
    group.append(el('legend', 'Important people'));
    group.append(el('p', 'Add the people MHM should understand when personalizing support. Helpful context can include how they support you, how often you connect, or anything sensitive MHM should keep in mind. Separate details with commas or semicolons.', { className: 'field-hint' }));
    const rows = el('div');
    const controls = [];
    function add(person = { name: '', type: '', relationships: [] }) {
      person = MHMSettingsInput.record(person);
      const row = el('div', null, { className: 'profile-person-row' });
      const id = `person-${crypto.randomUUID()}`;
      const name = field(row, 'Name', `${id}-name`, 'text', person.name, { required: '', maxlength: '100' });
      const type = field(row, 'Who they are to you', `${id}-type`, 'text', person.type, { maxlength: '100', placeholder: 'Family, friend, partner, healthcare provider…' });
      const relationships = field(row, 'Helpful context', `${id}-relationships`, 'text', MHMSettingsInput.list(person.relationships).join(', '), { maxlength: '1000', placeholder: 'Lives nearby; calls every Sunday; helps with appointments…' });
      const remove = el('button', 'Remove person', { type: 'button', className: 'plain-button danger-button' });
      const control = { row, name, type, relationships };
      remove.addEventListener('click', () => {
        controls.splice(controls.indexOf(control), 1);
        row.remove();
        parent.dispatchEvent(new Event('input', { bubbles: true }));
      });
      row.append(remove);
      controls.push(control);
      rows.append(row);
    }
    for (const person of MHMSettingsInput.list(initial)) add(person);
    const button = el('button', '+ Add important person', { type: 'button', className: 'plain-button' });
    button.addEventListener('click', () => {
      if (controls.length >= 30) return;
      add();
      controls.at(-1).name.focus();
    });
    group.append(rows, button);
    parent.append(group);
    return {
      read: () => controls.map(item => ({
        name: item.name.value.trim(),
        type: item.type.value.trim(),
        relationships: MHMSettingsInput.profileEntries(item.relationships.value),
      })),
    };
  }

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

  function customQuestionEditor(parent, initial, states, options) {
    initial = MHMSettingsInput.record(initial);
    states = MHMSettingsInput.record(states);
    options = MHMSettingsInput.record(options);
    const categories = MHMSettingsInput.record(options.question_categories);
    const categoryChoices = Object.entries(categories).map(([key, value]) => [key, MHMSettingsInput.record(value).name || key.replaceAll('_', ' ')]);
    if (!categoryChoices.length) categoryChoices.push(['mood', 'Mood'], ['energy', 'Energy'], ['health', 'Health'], ['activities', 'Activities']);
    if (!categoryChoices.some(([key]) => key === 'general')) categoryChoices.push(['general', 'General']);
    const templates = MHMSettingsInput.record(options.question_templates);
    const group = el('fieldset', null, { className: 'custom-question-editor' });
    group.append(el('legend', 'Custom questions'));
    group.append(el('p', 'Add questions that fit your routines, including numeric and paired-time answers. You can begin with a template or build your own.', { className: 'field-hint' }));
    const rows = el('div');
    const controls = [];
    const deleted = [];
    const undo = el('button', 'Undo last question deletion', { type: 'button', className: 'plain-button' });
    undo.hidden = true;
    function currentValue(item) {
      const validation = {};
      if (item.minimum.value !== '') validation.min = Number(item.minimum.value);
      if (item.maximum.value !== '') validation.max = Number(item.maximum.value);
      if (item.errorMessage.value.trim()) validation.error_message = item.errorMessage.value.trim();
      return {
        definition: {
          question_text: item.text.value.trim(), ui_display_name: item.displayName.value.trim(),
          type: item.type.value, category: item.category.value, validation,
        },
        state: item.frequency.value,
      };
    }
    function add(key, definition, state = 'off') {
      definition = MHMSettingsInput.record(definition);
      const validation = MHMSettingsInput.record(definition.validation);
      const row = el('div', null, { className: 'custom-question-row' });
      const text = field(row, 'Question', `${key}-text`, 'text', definition.question_text, { required: '', maxlength: '300' });
      const displayName = field(row, 'Short display name', `${key}-display-name`, 'text', definition.ui_display_name || definition.question_text, { required: '', maxlength: '150' });
      const type = select(row, 'Answer type', `${key}-type`, [['optional_text', 'Text'], ['yes_no', 'Yes or no'], ['scale_1_5', '1–5 scale'], ['number', 'Number'], ['time_pair', 'Two times']], definition.type || 'optional_text');
      const category = select(row, 'Category', `${key}-category`, categoryChoices, definition.category || categoryChoices[0][0]);
      const frequency = select(row, 'Include', `${key}-frequency`, [['off', 'Off'], ['always', 'Always'], ['sometimes', 'Sometimes']], state);
      const minimum = field(row, 'Minimum (optional)', `${key}-minimum`, 'number', validation.min, { step: 'any' });
      const maximum = field(row, 'Maximum (optional)', `${key}-maximum`, 'number', validation.max, { step: 'any' });
      const errorMessage = field(row, 'Validation message (optional)', `${key}-error`, 'text', validation.error_message, { maxlength: '300' });
      const remove = el('button', 'Remove question', { type: 'button', className: 'plain-button danger-button' });
      const control = { key, row, text, displayName, type, category, frequency, minimum, maximum, errorMessage };
      remove.addEventListener('click', () => {
        deleted.push({ key, ...currentValue(control) });
        controls.splice(controls.indexOf(control), 1);
        row.remove();
        undo.hidden = false;
        parent.dispatchEvent(new Event('input', { bubbles: true }));
      });
      row.append(remove);
      controls.push(control);
      rows.append(row);
    }
    for (const [key, definition] of Object.entries(initial)) add(key, definition, states[key] || 'sometimes');
    const templateChoices = [['', 'Blank question'], ...Object.entries(templates).map(([key, value]) => [key, MHMSettingsInput.record(value).ui_display_name || key.replaceAll('_', ' ')])];
    const template = select(group, 'Start from', 'custom-question-template', templateChoices, '');
    const button = el('button', '+ Add custom question', { type: 'button', className: 'plain-button' });
    button.addEventListener('click', () => {
      if (controls.length >= 20) return;
      const key = `custom_${crypto.randomUUID().replaceAll('-', '')}`;
      const chosen = template.value ? MHMSettingsInput.record(templates[template.value]) : null;
      add(key, chosen || { question_text: '', ui_display_name: '', type: 'optional_text', category: categoryChoices[0][0], validation: {} }, 'off');
      template.value = '';
      parent.dispatchEvent(new Event('input', { bubbles: true }));
      controls.at(-1).text.focus();
    });
    undo.addEventListener('click', () => {
      const item = deleted.pop();
      if (!item || controls.length >= 20) return;
      add(item.key, item.definition, item.state);
      undo.hidden = deleted.length === 0;
      parent.dispatchEvent(new Event('input', { bubbles: true }));
    });
    group.append(rows, button, undo);
    parent.append(group);
    return {
      read() {
        return {
          customQuestions: Object.fromEntries(controls.map(item => [item.key, currentValue(item).definition])),
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
    const deleted = [];
    const undo = el('button', 'Undo last window deletion', { type: 'button', className: 'plain-button' });
    undo.hidden = true;
    function currentValue(item) {
      const selected = item.dayInputs.filter(([, input]) => input.checked).map(([day]) => day);
      return { name: item.input.value, value: { active: item.enabled.checked, days: selected.length === 7 ? ['ALL'] : selected, start_time: item.start.value, end_time: item.end.value } };
    }
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
      remove.addEventListener('click', () => {
        deleted.push(currentValue(control));
        controls.splice(controls.indexOf(control), 1);
        row.remove();
        undo.hidden = false;
        parent.dispatchEvent(new Event('input', { bubbles: true }));
      });
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
    undo.addEventListener('click', () => {
      const item = deleted.pop();
      if (!item || controls.length >= 20) return;
      add(item.name, item.value);
      undo.hidden = deleted.length === 0;
      parent.dispatchEvent(new Event('input', { bubbles: true }));
    });
    group.append(rows, button, undo);
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
  function validateSettingsData(data) {
    const payload = MHMSettingsInput.record(data);
    const sections = MHMSettingsInput.record(payload.sections);
    const revisions = MHMSettingsInput.record(payload.revisions);
    MHMSettingsInput.record(payload.options);
    MHMSettingsInput.record(payload.available_message_periods);
    for (const section of Object.keys(titles)) {
      if (!Object.hasOwn(sections, section) || typeof revisions[section] !== 'string') {
        throw new Error('MHM received settings data that does not match the current format.');
      }
      MHMSettingsInput.record(sections[section]);
    }
    return payload;
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
    return validateSettingsData(data);
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
      const lovedOnes = lovedOnesEditor(form, values.loved_ones);
      form.append(el('p', 'Health details are optional and are used only to personalize MHM support.', { className: 'field-hint' }));
      read = () => ({ preferred_name: name.value, date_of_birth: birthDate.value, ...Object.fromEntries(Object.entries(fields).map(([key, input]) => [key, lines(input)])), loved_ones: lovedOnes.read() });
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
          const savedPattern = recurring.default_recurrence_pattern || '';
          const savedInterval = Number(recurring.default_recurrence_interval ?? 1);
          const presetPattern = savedInterval === 1 && ['daily', 'weekly', 'monthly'].includes(savedPattern) ? savedPattern : savedPattern ? 'custom' : '';
          const pattern = select(details, 'Default repeat for new tasks', 'recurrence-pattern', [['', 'Does not repeat'], ['daily', 'Every day'], ['weekly', 'Every week'], ['monthly', 'Every month'], ['custom', 'Custom…']], presetPattern);
          const customRepeat = el('div', null, { className: 'settings-two-col' });
          const interval = field(customRepeat, 'Repeat every', 'recurrence-interval', 'number', savedInterval, { min: '1', max: '365', required: '' });
          const unit = select(customRepeat, 'Unit', 'recurrence-unit', [['daily', 'Day(s)'], ['weekly', 'Week(s)'], ['monthly', 'Month(s)'], ['yearly', 'Year(s)']], savedPattern || 'daily');
          details.append(customRepeat);
          const after = field(details, 'Count the next repeat from completion', 'repeat-after', 'checkbox', recurring.default_repeat_after_completion);
          const syncRepeatDefaults = () => {
            const repeats = Boolean(pattern.value);
            const isCustom = pattern.value === 'custom';
            customRepeat.hidden = !isCustom;
            interval.disabled = !isCustom;
            unit.disabled = !isCustom;
            after.parentElement.hidden = !repeats;
            after.disabled = !repeats;
          };
          pattern.addEventListener('change', syncRepeatDefaults);
          syncRepeatDefaults();
          details.append(el('p', 'These defaults apply to new tasks. Existing tasks keep their own repeat settings.', { className: 'field-hint' }));
          read = () => {
            const recurrencePattern = pattern.value === 'custom' ? unit.value : pattern.value || null;
            return { enabled: enabled.checked, periods: periods.read(), recurring: { default_recurrence_pattern: recurrencePattern, default_recurrence_interval: pattern.value === 'custom' ? Number(interval.value) : 1, default_repeat_after_completion: recurrencePattern ? after.checked : false } };
          };
        } else {
          const standardQuestions = MHMSettingsInput.record(data.options.questions);
          const customQuestions = MHMSettingsInput.record(values.custom_questions);
          const questionStates = MHMSettingsInput.record(values.questions);
          const questions = {};
          const questionGroups = MHMSettingsInput.questionGroups(standardQuestions, customQuestions, data.options.question_category_map, data.options.question_categories);
          const groupLayout = el('div', null, { className: 'checkin-question-groups' });
          for (const group of questionGroups) {
            const questionGroup = el('fieldset', null, { className: 'checkin-question-group' });
            questionGroup.append(el('legend', group.name));
            if (group.description) questionGroup.append(el('p', group.description, { className: 'field-hint' }));
            for (const { key, label } of group.questions) {
              questions[key] = select(questionGroup, label, `question-${key}`, [['off', 'Off'], ['always', 'Always'], ['sometimes', 'Sometimes']], questionStates[key]);
              questions[key].parentElement.classList.add('checkin-question-row');
            }
            groupLayout.append(questionGroup);
          }
          details.append(groupLayout);
          const custom = customQuestionEditor(details, customQuestions, questionStates, data.options);
          const counts = el('div', null, { className: 'settings-two-col' });
          const minimum = field(counts, 'Minimum questions', 'min-questions', 'number', values.min_questions, { min: '1', max: '100', required: '' });
          const maximum = field(counts, 'Maximum questions', 'max-questions', 'number', values.max_questions, { min: '1', max: '100', required: '' });
          details.append(counts, el('p', 'Include all Always questions. With Sometimes questions, the minimum must leave at least one out so check-ins can vary.', { className: 'field-hint' }));
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
          const reducedMotion = typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
          MHMSettingsInput.scrollToSection(document.getElementById('settings'), reducedMotion);
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
