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

test('signed-in page logos return to the account home', async () => {
  for (const page of ['app', 'tasks', 'notes', 'messages', 'insights']) {
    const html = await readFile(new URL(`./${page}.html`, import.meta.url), 'utf8');
    assert.match(html, /class="brand" href="app\.html" aria-label="MHM account home"/);
  }
});

test('feature details and custom check-in controls are present', async () => {
  assert.match(source, /details\.disabled = !enabled\.checked/);
  assert.match(source, /\+ Add custom question/);
  assert.match(source, /custom_\$\{crypto\.randomUUID\(\)/);
  assert.match(source, /category === 'tasks'[\s\S]*'15:00'[\s\S]*'17:00'/);
  assert.match(source, /category === 'checkin'[\s\S]*'09:30'[\s\S]*'11:30'/);
});
