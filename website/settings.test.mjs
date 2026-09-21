import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./settings.js', import.meta.url), 'utf8');
const helperSource = `${source.slice(0, source.indexOf('(() =>'))}\nthis.helpers = MHMSettingsInput;`;
const context = vm.createContext({});
vm.runInContext(helperSource, context);

test('profile entries accept lines, commas, and semicolons', () => {
  assert.deepEqual(
    [...context.helpers.profileEntries('walking, reading; music\nfamily\n\n')],
    ['walking', 'reading', 'music', 'family'],
  );
});

test('settings collections must use the current schema', () => {
  assert.throws(() => context.helpers.record(undefined), /current object format/);
  assert.throws(() => context.helpers.record(null), /current object format/);
  assert.throws(() => context.helpers.list(undefined), /current list format/);
  assert.throws(() => context.helpers.list({}), /current list format/);
  assert.throws(() => context.helpers.profileEntries(null), /must be text/);
});

test('standard check-in questions are grouped by category', () => {
  const groups = context.helpers.questionGroups(
    { mood: 'Mood', stress: 'Stress', hydration: 'Hydration', custom_one: 'Custom' },
    { custom_one: {} },
    { mood: 'mood', stress: 'mood', hydration: 'health' },
    { mood: { name: 'Mood', description: 'Feelings' }, health: { name: 'Health' } },
  );
  assert.deepEqual(
    JSON.parse(JSON.stringify(groups)),
    [
      { key: 'mood', name: 'Mood', description: 'Feelings', questions: [{ key: 'mood', label: 'Mood' }, { key: 'stress', label: 'Stress' }] },
      { key: 'health', name: 'Health', description: '', questions: [{ key: 'hydration', label: 'Hydration' }] },
    ],
  );
});

test('clicking date and time inputs opens the native picker when available', () => {
  let opened = 0;
  context.helpers.openPicker({ disabled: false, readOnly: false, showPicker() { opened++; } });
  context.helpers.openPicker({ disabled: true, readOnly: false, showPicker() { opened++; } });
  context.helpers.openPicker({ disabled: false, readOnly: true, showPicker() { opened++; } });
  assert.equal(opened, 1);
});

test('date and time inputs open on the initial pointer action', () => {
  let opened = 0;
  const listeners = {};
  const input = {
    disabled: false,
    readOnly: false,
    showPicker() { opened++; },
    addEventListener(type, listener) { listeners[type] = listener; },
  };
  context.helpers.bindPicker(input);
  listeners.pointerdown({ button: 2 });
  assert.equal(opened, 0);
  listeners.pointerdown({ button: 0 });
  assert.equal(opened, 1);
});

test('changing settings sections returns to the settings heading', () => {
  let options;
  context.helpers.scrollToSection({ scrollIntoView(value) { options = value; } });
  assert.deepEqual({ ...options }, { behavior: 'smooth', block: 'start' });
  context.helpers.scrollToSection({ scrollIntoView(value) { options = value; } }, true);
  assert.deepEqual({ ...options }, { behavior: 'auto', block: 'start' });
});

test('signed-in page logos return to home', async () => {
  for (const page of ['home', 'app', 'tasks', 'notes', 'messages', 'insights', 'setup']) {
    const html = await readFile(new URL(`./${page}.html`, import.meta.url), 'utf8');
    assert.match(html, /class="brand" href="home\.html" aria-label="MHM home"/);
  }
});

test('feature details and custom check-in controls are present', async () => {
  assert.match(source, /details\.disabled = !enabled\.checked/);
  assert.match(source, /\+ Add custom question/);
  assert.match(source, /custom_\$\{crypto\.randomUUID\(\)/);
  assert.match(source, /category === 'tasks'[\s\S]*'15:00'[\s\S]*'17:00'/);
  assert.match(source, /category === 'checkin'[\s\S]*'09:30'[\s\S]*'11:30'/);
  assert.match(source, /const customQuestions = MHMSettingsInput\.record\(values\.custom_questions\)/);
  assert.doesNotMatch(source, /completeSettingsData/);
});

test('important-person prompts distinguish roles from useful context', () => {
  assert.match(source, /Family, friend, partner, healthcare provider/);
  assert.match(source, /Lives nearby; calls every Sunday; helps with appointments/);
  assert.doesNotMatch(source, /Sister, caregiver, emergency contact/);
});
