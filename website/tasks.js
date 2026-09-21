const MHMTaskInput = Object.freeze({
  withTag(value, tag) {
    const tags = String(value || '').split(',').map(item => item.trim()).filter(Boolean);
    const newTag = String(tag || '').trim();
    if (newTag && !tags.some(item => item.toLowerCase() === newTag.toLowerCase())) tags.push(newTag);
    return tags.join(', ');
  },
});

(() => {
  const status = document.getElementById('tasks-status');
  const workspace = document.getElementById('tasks-workspace');
  const list = document.getElementById('task-list');
  const empty = document.getElementById('task-empty');
  const count = document.getElementById('tasks-count');
  const summary = document.getElementById('task-list-summary');
  const createForm = document.getElementById('task-create-form');
  const tabs = [...document.querySelectorAll('[data-task-view]')];
  const dueSoon = document.getElementById('task-due-soon');
  const selectedCount = document.getElementById('task-selected-count');
  const bulkPrimary = document.getElementById('task-bulk-primary');
  const bulkDelete = document.getElementById('task-bulk-delete');
  let view = 'active';
  let tasks = [];
  let templates = [];
  let existingTags = [];
  let dueSoonCount = 0;
  const selected = new Set();
  const quickReminderOptions = [
    ['5-10min', '5–10 minutes'], ['30min-1hour', '30–60 minutes'], ['1-2hour', '1–2 hours'],
    ['1-2day', '1–2 days'], ['3-5day', '3–5 days'], ['1-2week', '1–2 weeks'],
  ];

  function populateTagPicker(picker, values) {
    picker.replaceChildren(new Option('Choose a tag…', ''), ...values.map(value => new Option(value, value)));
  }

  function bindTagPicker(input, picker) {
    picker.addEventListener('change', () => {
      if (!picker.value) return;
      input.value = MHMTaskInput.withTag(input.value, picker.value);
      picker.value = '';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.focus();
    });
  }

  function recurrenceChoice(pattern, interval) {
    if (!pattern) return '';
    return Number(interval || 1) === 1 && ['daily', 'weekly', 'monthly'].includes(pattern) ? pattern : 'custom';
  }

  function syncRecurrenceControls(choice, options, custom, interval, unit, repeatAfter) {
    const repeats = Boolean(choice.value);
    const isCustom = choice.value === 'custom';
    options.hidden = !repeats;
    custom.hidden = !isCustom;
    interval.disabled = !isCustom;
    unit.disabled = !isCustom;
    repeatAfter.disabled = !repeats;
  }

  function readRecurrence(choice, interval, unit) {
    if (!choice.value) return { pattern: null, interval: 1 };
    if (choice.value === 'custom') {
      return { pattern: unit.value, interval: Number(interval.value || 1) };
    }
    return { pattern: choice.value, interval: 1 };
  }

  function showStatus(message, error = false) {
    status.textContent = message;
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
    if (!response.ok) {
      const error = new Error(result.error || 'MHM could not update your tasks. Please try again.');
      error.status = response.status;
      throw error;
    }
    return result;
  }

  function button(label, className, onClick) {
    const action = document.createElement('button');
    action.type = 'button'; action.className = className; action.textContent = label;
    action.addEventListener('click', onClick);
    return action;
  }

  function dueText(task) {
    if (!task.due_date) return 'No due date';
    return `Due ${task.due_date}${task.due_time ? ` at ${task.due_time}` : ''}`;
  }

  function recurrenceText(task) {
    const pattern = task.recurrence && task.recurrence.pattern;
    if (!pattern) return '';
    const interval = task.recurrence.interval || 1;
    return interval === 1 ? `Repeats ${pattern}` : `Repeats every ${interval} ${pattern}`;
  }

  function tagsText(task) {
    return Array.isArray(task.tags) && task.tags.length ? `Tags: ${task.tags.join(', ')}` : '';
  }

  function remindersText(task) {
    const reminders = Array.isArray(task.reminders) ? task.reminders : [];
    const periods = reminders.filter(item => item && item.kind === 'scheduled' && item.period).map(item => item.period);
    const quick = reminders.filter(item => item && item.kind === 'quick').map(item => new Map(quickReminderOptions).get(item.value) || item.value);
    const shown = periods.slice(0, 2).map(period => `${period.date} ${period.start_time}${period.end_time ? `–${period.end_time}` : ''}`);
    const details = [];
    if (shown.length) details.push(`${shown.join(', ')}${periods.length > 2 ? ` (+${periods.length - 2} more)` : ''}`);
    if (quick.length) details.push(`relative: ${quick.join(', ')}`);
    return details.length ? `Reminders: ${details.join('; ')}` : '';
  }
  function addReminderRow(parent, period = {}) {
    const row = document.createElement('div'); row.className = 'task-reminder-row';
    const date = input(row, 'Date', 'date', period.date, `reminder-date-${Math.random().toString(36).slice(2)}`);
    const start = input(row, 'Time', 'time', period.start_time, `reminder-start-${Math.random().toString(36).slice(2)}`);
    const end = input(row, 'End (optional)', 'time', period.end_time, `reminder-end-${Math.random().toString(36).slice(2)}`);
    const remove = button('Remove', 'plain-button task-reminder-remove', () => row.remove());
    row.append(remove); parent.append(row);
    return { date, start, end };
  }

  function readReminderPeriods(parent) {
    return [...parent.querySelectorAll('.task-reminder-row')].map(row => ({
      date: row.querySelector('input[type="date"]')?.value || '',
      start_time: row.querySelectorAll('input[type="time"]')[0]?.value || '',
      end_time: row.querySelectorAll('input[type="time"]')[1]?.value || '',
    })).filter(period => period.date || period.start_time || period.end_time);
  }

  function render() {
    list.replaceChildren();
    count.textContent = `${tasks.length} ${view === 'active' ? 'active' : 'completed'} ${tasks.length === 1 ? 'task' : 'tasks'}`;
    summary.textContent = view === 'active' ? 'Make room for the next small step.' : 'You did these.';
    dueSoon.textContent = `${dueSoonCount} active ${dueSoonCount === 1 ? 'task is' : 'tasks are'} due in the next 7 days`;
    bulkPrimary.textContent = view === 'active' ? 'Complete selected' : 'Restore selected';
    empty.hidden = tasks.length !== 0;
    for (const task of tasks) {
      const article = document.createElement('article');
      article.className = `task-card${view === 'completed' ? ' is-completed' : ''}`;
      const chooser = document.createElement('label'); chooser.className = 'task-select';
      const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.checked = selected.has(task.id); checkbox.setAttribute('aria-label', `Select ${task.title}`);
      checkbox.addEventListener('change', () => { checkbox.checked ? selected.add(task.id) : selected.delete(task.id); updateBulkActions(); });
      chooser.append(checkbox);
      const content = document.createElement('div'); content.className = 'task-card-content';
      const title = document.createElement('h3'); title.textContent = task.title; content.append(title);
      if (task.description) { const description = document.createElement('p'); description.textContent = task.description; content.append(description); }
      const meta = document.createElement('div'); meta.className = 'task-meta';
      const due = document.createElement('span'); due.textContent = dueText(task); meta.append(due);
      const priority = document.createElement('span'); priority.className = `priority priority-${task.priority}`; priority.textContent = task.priority; meta.append(priority);
      const repeat = recurrenceText(task); if (repeat) { const recurring = document.createElement('span'); recurring.textContent = repeat; meta.append(recurring); }
      const tags = tagsText(task); if (tags) { const tagLabel = document.createElement('span'); tagLabel.textContent = tags; meta.append(tagLabel); }
      const reminders = remindersText(task); if (reminders) { const reminderLabel = document.createElement('span'); reminderLabel.textContent = reminders; meta.append(reminderLabel); }
      if (view === 'completed' && task.completion && task.completion.completed_at) {
        const completed = document.createElement('span'); completed.textContent = `Completed ${String(task.completion.completed_at).replace('T', ' ')}`; meta.append(completed);
      }
      if (view === 'completed' && task.completion && task.completion.notes) {
        const notes = document.createElement('p'); notes.className = 'task-completion-notes'; notes.textContent = `Completion notes: ${task.completion.notes}`; content.append(notes);
      }
      content.append(meta);
      const actions = document.createElement('div'); actions.className = 'task-actions';
      if (view === 'active') {
        actions.append(button('Edit', 'plain-button', () => openEditor(task)));
        actions.append(button('More', 'plain-button', () => openSupportActions(task)));
        actions.append(button('Complete', 'button task-action-primary', () => openCompletionDialog(task)));
      } else {
        actions.append(button('Restore', 'plain-button', () => changeTask(task, 'restore')));
      }
      actions.append(button('Delete', 'plain-button task-delete', () => removeTask(task)));
      article.append(chooser, content, actions); list.append(article);
    }
    updateBulkActions();
  }

  async function load() {
    try {
      const result = await api(`/api/tasks?status=${view}`);
      tasks = result.tasks || [];
      existingTags = result.tags || [];
      populateTagPicker(document.getElementById('task-existing-tag'), existingTags);
      dueSoonCount = result.due_soon_count || 0;
      selected.clear();
      workspace.hidden = false; showStatus(''); render();
    } catch (error) {
      workspace.hidden = error.status === 403;
      showStatus(error.message, true);
    }
  }

  async function changeTask(task, action) {
    try { await api(`/api/tasks/${encodeURIComponent(task.id)}/${action}`, 'POST', {}); await load(); }
    catch (error) { showStatus(error.message, true); }
  }

  function updateBulkActions() {
    selectedCount.textContent = `${selected.size} selected`;
    bulkPrimary.disabled = selected.size === 0;
    bulkDelete.disabled = selected.size === 0;
  }

  async function runBulk(action) {
    if (!selected.size) return;
    const label = action === 'delete' ? 'delete' : action;
    if (!window.confirm(`${label[0].toUpperCase()}${label.slice(1)} ${selected.size} selected ${selected.size === 1 ? 'task' : 'tasks'}?`)) return;
    try {
      const result = await api(`/api/tasks/bulk/${action}`, 'POST', { task_ids: [...selected] });
      await load();
      showStatus(result.failed && result.failed.length ? `${result.changed.length} updated; ${result.failed.length} could not be changed.` : `${result.changed.length} ${result.changed.length === 1 ? 'task' : 'tasks'} updated.`);
    } catch (error) { showStatus(error.message, true); }
  }

  function localDateTime() {
    const now = new Date();
    const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString();
    return { date: local.slice(0, 10), time: local.slice(11, 16) };
  }

  function openCompletionDialog(task) {
    const defaults = localDateTime();
    const dialog = document.createElement('dialog'); dialog.className = 'task-dialog';
    const heading = document.createElement('h2'); heading.textContent = `Complete “${task.title}”`;
    const form = document.createElement('form'); form.className = 'task-edit-form';
    const row = document.createElement('div'); row.className = 'task-form-row';
    const date = input(row, 'Completion date', 'date', defaults.date, 'complete-date'); date.required = true;
    const time = input(row, 'Completion time', 'time', defaults.time, 'complete-time'); time.required = true;
    form.append(row);
    const notes = input(form, 'Completion notes (optional)', 'textarea', '', 'complete-notes'); notes.maxLength = 5000;
    const actions = document.createElement('div'); actions.className = 'task-dialog-actions';
    actions.append(button('Cancel', 'plain-button', () => dialog.close()));
    const save = document.createElement('button'); save.type = 'submit'; save.className = 'button'; save.textContent = 'Complete task'; actions.append(save);
    form.append(actions); dialog.append(heading, form); document.body.append(dialog);
    form.addEventListener('submit', async event => {
      event.preventDefault(); save.disabled = true;
      try {
        await api(`/api/tasks/${encodeURIComponent(task.id)}/complete`, 'POST', { completion_date: date.value, completion_time: time.value, completion_notes: notes.value });
        dialog.close(); await load();
      } catch (error) { showStatus(error.message, true); save.disabled = false; }
    });
    dialog.addEventListener('close', () => dialog.remove(), { once: true });
    if (typeof dialog.showModal === 'function') dialog.showModal(); else dialog.setAttribute('open', '');
  }

  async function runSupportAction(task, action, payload, dialog) {
    try {
      const result = await api(`/api/tasks/${encodeURIComponent(task.id)}/${action}`, 'POST', payload);
      dialog.close();
      await load();
      showStatus(result.message || 'Task updated.');
    } catch (error) { showStatus(error.message, true); }
  }

  function openSupportActions(task) {
    const dialog = document.createElement('dialog'); dialog.className = 'task-dialog';
    const heading = document.createElement('h2'); heading.textContent = `Help with “${task.title}”`;
    const copy = document.createElement('p'); copy.textContent = 'Delay the reminder without moving the due date, skip this occurrence, or turn it into a smaller next step.';
    const actions = document.createElement('div'); actions.className = 'task-support-actions';
    actions.append(
      button('Remind me in 1 hour', 'plain-button', () => runSupportAction(task, 'snooze', { option: '1_hour' }, dialog)),
      button('Remind me tonight', 'plain-button', () => runSupportAction(task, 'snooze', { option: 'tonight' }, dialog)),
      button('Remind me next week', 'plain-button', () => runSupportAction(task, 'snooze', { option: 'next_week' }, dialog)),
      button('Skip this occurrence', 'plain-button', () => {
        if (window.confirm(`Skip this occurrence of “${task.title}”? It will not be marked complete.`)) runSupportAction(task, 'skip', {}, dialog);
      }),
    );
    const simplify = document.createElement('div'); simplify.className = 'settings-field';
    const label = document.createElement('label'); label.htmlFor = 'simplify-title'; label.textContent = 'A smaller next step';
    const smaller = document.createElement('input'); smaller.id = 'simplify-title'; smaller.maxLength = 500; smaller.placeholder = 'e.g. Put the dishes beside the sink';
    const simplifyButton = button('Simplify task', 'button', () => {
      if (smaller.value.trim()) runSupportAction(task, 'simplify', { new_title: smaller.value.trim() }, dialog);
      else { smaller.setCustomValidity('Enter a smaller next step.'); smaller.reportValidity(); }
    });
    smaller.addEventListener('input', () => smaller.setCustomValidity(''));
    simplify.append(label, smaller, simplifyButton);
    const close = button('Close', 'plain-button', () => dialog.close());
    dialog.append(heading, copy, actions, simplify, close); document.body.append(dialog);
    dialog.addEventListener('close', () => dialog.remove(), { once: true });
    if (typeof dialog.showModal === 'function') dialog.showModal(); else dialog.setAttribute('open', '');
  }

  async function loadTemplates() {
    try {
      const result = await api('/api/task-templates');
      templates = result.templates || [];
      const select = document.getElementById('task-template');
      for (const template of templates) {
        const option = document.createElement('option'); option.value = template.id; option.textContent = template.name; select.append(option);
      }
    } catch (error) { showStatus(error.message, true); }
  }

  async function removeTask(task) {
    if (!window.confirm(`Delete “${task.title}”? This cannot be undone.`)) return;
    try { await api(`/api/tasks/${encodeURIComponent(task.id)}`, 'DELETE', {}); await load(); }
    catch (error) { showStatus(error.message, true); }
  }

  function input(parent, labelText, type, value, id) {
    const wrapper = document.createElement('div'); wrapper.className = 'settings-field';
    const label = document.createElement('label'); label.htmlFor = id; label.textContent = labelText;
    const field = type === 'textarea' ? document.createElement('textarea') : document.createElement('input');
    field.id = id; field.name = id; field.value = value || '';
    if (type === 'textarea') field.rows = 3; else field.type = type;
    if (type === 'date' || type === 'time') {
      field.addEventListener('pointerdown', event => {
        if (typeof event.button === 'number' && event.button !== 0) return;
        if (typeof field.showPicker === 'function') try { field.showPicker(); } catch (_) { /* Native icon remains available. */ }
      });
    }
    wrapper.append(label, field); parent.append(wrapper); return field;
  }

  function select(parent, labelText, value, id, options) {
    const wrapper = document.createElement('div'); wrapper.className = 'settings-field';
    const label = document.createElement('label'); label.htmlFor = id; label.textContent = labelText;
    const field = document.createElement('select'); field.id = id; field.name = id;
    for (const [optionValue, optionLabel] of options) {
      const option = document.createElement('option'); option.value = optionValue; option.textContent = optionLabel;
      field.append(option);
    }
    field.value = value || '';
    wrapper.append(label, field); parent.append(wrapper); return field;
  }

  function reminderEditor(parent, reminders = []) {
    const fieldset = document.createElement('fieldset'); fieldset.className = 'task-reminders';
    const legend = document.createElement('legend'); legend.textContent = 'Task reminders'; fieldset.append(legend);
    const help = document.createElement('p'); help.className = 'field-help'; help.textContent = 'Choose a relative reminder or add a specific date and time. End time is optional.'; fieldset.append(help);
    const choices = document.createElement('div'); choices.className = 'task-quick-reminders';
    const selectedValues = reminders.filter(item => item && item.kind === 'quick').map(item => item.value);
    const inputs = quickReminderOptions.map(([value, labelText]) => {
      const label = document.createElement('label'); const checkbox = document.createElement('input');
      checkbox.type = 'checkbox'; checkbox.value = value; checkbox.checked = selectedValues.includes(value);
      label.append(checkbox, document.createTextNode(` ${labelText}`)); choices.append(label); return checkbox;
    });
    const reminderList = document.createElement('div'); reminderList.className = 'task-reminder-list';
    reminders.filter(item => item && item.kind === 'scheduled' && item.period).forEach(item => addReminderRow(reminderList, item.period));
    fieldset.append(choices, reminderList, button('+ Add a custom reminder', 'plain-button', () => addReminderRow(reminderList)));
    parent.append(fieldset);
    return {
      readQuick: () => inputs.filter(item => item.checked).map(item => item.value),
      readScheduled: () => readReminderPeriods(reminderList),
    };
  }

  function openEditor(task) {
    const dialog = document.createElement('dialog'); dialog.className = 'task-dialog';
    const heading = document.createElement('h2'); heading.textContent = 'Edit task';
    const form = document.createElement('form'); form.className = 'task-edit-form';
    const title = input(form, 'Task title', 'text', task.title, 'edit-title'); title.required = true; title.maxLength = 500;
    const description = input(form, 'Details', 'textarea', task.description, 'edit-description'); description.maxLength = 10000;
    const row = document.createElement('div'); row.className = 'task-form-row';
    const date = input(row, 'Due date', 'date', task.due_date, 'edit-due-date');
    const time = input(row, 'Time', 'time', task.due_time, 'edit-due-time');
    const priority = select(row, 'Priority', task.priority, 'edit-priority', [['low', 'Low'], ['medium', 'Medium'], ['high', 'High'], ['urgent', 'Urgent'], ['critical', 'Critical']]);
    form.append(row);
    const pattern = task.recurrence && task.recurrence.pattern;
    const savedInterval = task.recurrence && task.recurrence.interval || 1;
    const recurrence = select(form, 'Repeat', recurrenceChoice(pattern, savedInterval), 'edit-recurrence', [['', 'Does not repeat'], ['daily', 'Every day'], ['weekly', 'Every week'], ['monthly', 'Every month'], ['custom', 'Custom…']]);
    const recurrenceOptions = document.createElement('div'); recurrenceOptions.className = 'task-form-row task-recurrence-options';
    const customRecurrence = document.createElement('div'); customRecurrence.className = 'task-custom-recurrence';
    const interval = input(customRecurrence, 'Repeat every', 'number', savedInterval, 'edit-recurrence-interval'); interval.min = 1; interval.max = 365;
    const unit = select(customRecurrence, 'Unit', pattern || 'daily', 'edit-recurrence-unit', [['daily', 'Day(s)'], ['weekly', 'Week(s)'], ['monthly', 'Month(s)'], ['yearly', 'Year(s)']]);
    const afterWrapper = document.createElement('label'); afterWrapper.className = 'task-inline-check';
    const repeatAfter = document.createElement('input'); repeatAfter.type = 'checkbox'; repeatAfter.checked = !task.recurrence || task.recurrence.repeat_after_completion !== false;
    afterWrapper.append(repeatAfter, document.createTextNode(' Count the next repeat from completion')); recurrenceOptions.append(customRecurrence, afterWrapper); form.append(recurrenceOptions);
    const syncEditorRecurrence = () => syncRecurrenceControls(recurrence, recurrenceOptions, customRecurrence, interval, unit, repeatAfter);
    recurrence.addEventListener('change', syncEditorRecurrence); syncEditorRecurrence();
    const tags = input(form, 'Tags', 'text', Array.isArray(task.tags) ? task.tags.join(', ') : '', 'edit-tags');
    tags.maxLength = 1000; tags.placeholder = 'health, errands, home';
    const existingTag = select(form, 'Add an existing tag', '', 'edit-existing-tag', [['', 'Choose a tag…'], ...existingTags.map(value => [value, value])]);
    bindTagPicker(tags, existingTag);
    const reminders = reminderEditor(form, Array.isArray(task.reminders) ? task.reminders : []);
    const actions = document.createElement('div'); actions.className = 'task-dialog-actions';
    actions.append(button('Cancel', 'plain-button', () => dialog.close()));
    const save = document.createElement('button'); save.type = 'submit'; save.className = 'button'; save.textContent = 'Save changes'; actions.append(save);
    form.append(actions); dialog.append(heading, form); document.body.append(dialog);
    form.addEventListener('submit', async event => {
      event.preventDefault(); save.disabled = true;
      try {
        const recurrenceValue = readRecurrence(recurrence, interval, unit);
        await api(`/api/tasks/${encodeURIComponent(task.id)}`, 'PATCH', {
          title: title.value.trim(), description: description.value,
          due_date: date.value || null, due_time: time.value || null, priority: priority.value.trim().toLowerCase(),
          recurrence_pattern: recurrenceValue.pattern,
          recurrence_interval: recurrenceValue.interval, repeat_after_completion: recurrenceValue.pattern ? repeatAfter.checked : false,
          tags: tags.value.split(',').map(tag => tag.trim()).filter(Boolean),
          reminder_periods: reminders.readScheduled(),
          quick_reminders: reminders.readQuick(),
        });
        dialog.close(); await load();
      } catch (error) { showStatus(error.message, true); save.disabled = false; }
    });
    dialog.addEventListener('close', () => dialog.remove(), { once: true });
    if (typeof dialog.showModal === 'function') dialog.showModal(); else dialog.setAttribute('open', '');
    title.focus();
  }

  const createRecurrence = document.getElementById('task-recurrence');
  const createRecurrenceOptions = document.getElementById('task-recurrence-options');
  const createCustomRecurrence = document.getElementById('task-custom-recurrence');
  const createRecurrenceInterval = document.getElementById('task-recurrence-interval');
  const createRecurrenceUnit = document.getElementById('task-recurrence-unit');
  const createRepeatAfter = document.getElementById('task-repeat-after-completion');
  const createTagInput = document.getElementById('task-tags');
  const createTagPicker = document.getElementById('task-existing-tag');
  const extraFields = document.getElementById('task-extra-fields');
  const moreOptions = document.getElementById('task-more-options');
  const syncCreateRecurrence = () => syncRecurrenceControls(createRecurrence, createRecurrenceOptions, createCustomRecurrence, createRecurrenceInterval, createRecurrenceUnit, createRepeatAfter);
  function setExtraFieldsOpen(open) {
    extraFields.hidden = !open;
    moreOptions.setAttribute('aria-expanded', String(open));
    moreOptions.textContent = open ? 'Fewer options' : 'More options';
  }
  createRecurrence.addEventListener('change', syncCreateRecurrence);
  moreOptions.addEventListener('click', () => setExtraFieldsOpen(extraFields.hidden));
  bindTagPicker(createTagInput, createTagPicker);
  syncCreateRecurrence();

  function resetCreateForm() {
    createForm.reset();
    createRecurrenceInterval.value = '1';
    createRecurrenceUnit.value = 'daily';
    createRepeatAfter.checked = true;
    document.getElementById('task-reminder-list').replaceChildren();
    syncCreateRecurrence();
    setExtraFieldsOpen(false);
  }

  createForm.addEventListener('submit', async event => {
    event.preventDefault();
    const submit = createForm.querySelector('button[type="submit"]'); submit.disabled = true; showStatus('Adding task…');
    const form = new FormData(createForm);
    try {
      const recurrence = readRecurrence(createRecurrence, createRecurrenceInterval, createRecurrenceUnit);
      await api('/api/tasks', 'POST', {
        title: String(form.get('title') || '').trim(), description: String(form.get('description') || ''),
        due_date: form.get('due_date') || null, due_time: form.get('due_time') || null,
        priority: form.get('priority') || 'medium', recurrence_pattern: recurrence.pattern,
        recurrence_interval: recurrence.interval, repeat_after_completion: recurrence.pattern ? createRepeatAfter.checked : false,
        tags: String(form.get('tags') || '').split(',').map(tag => tag.trim()).filter(Boolean),
        reminder_periods: readReminderPeriods(document.getElementById('task-reminder-list')),
        quick_reminders: form.getAll('quick_reminders'),
      });
      resetCreateForm(); showStatus(''); await load();
    } catch (error) { showStatus(error.message, true); }
    finally { submit.disabled = false; }
  });
  document.getElementById('task-add-reminder').addEventListener('click', () => addReminderRow(document.getElementById('task-reminder-list')));
  document.getElementById('task-template').addEventListener('change', event => {
    const templateId = event.target.value;
    const template = templates.find(item => item.id === templateId);
    resetCreateForm();
    event.target.value = templateId;
    if (!template) { setExtraFieldsOpen(false); document.getElementById('task-title').focus(); return; }
    setExtraFieldsOpen(true);
    document.getElementById('task-title').value = template.title || '';
    document.getElementById('task-description').value = template.description || '';
    document.getElementById('task-priority').value = template.priority || 'medium';
    createRecurrence.value = recurrenceChoice(template.recurrence_pattern, template.recurrence_interval);
    createRecurrenceInterval.value = template.recurrence_interval || 1;
    createRecurrenceUnit.value = template.recurrence_pattern || 'daily';
    syncCreateRecurrence();
    document.getElementById('task-tags').value = (template.tags || []).join(', ');
    document.getElementById('task-due-time').value = template.due_time || '';
  });
  bulkPrimary.addEventListener('click', () => runBulk(view === 'active' ? 'complete' : 'restore'));
  bulkDelete.addEventListener('click', () => runBulk('delete'));
  for (const picker of document.querySelectorAll('input[type="date"], input[type="time"]')) {
    picker.addEventListener('pointerdown', event => {
      if (typeof event.button === 'number' && event.button !== 0) return;
      if (typeof picker.showPicker === 'function') try { picker.showPicker(); } catch (_) { /* Native icon remains available. */ }
    });
  }
  for (const tab of tabs) tab.addEventListener('click', () => { view = tab.dataset.taskView; tabs.forEach(item => item.setAttribute('aria-selected', String(item === tab))); load(); });
  loadTemplates();
  load();
})();
