import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./tasks.js', import.meta.url), 'utf8');
const helperSource = `${source.slice(0, source.indexOf('(() =>'))}\nthis.helpers = MHMTaskInput;`;
const context = vm.createContext({});
vm.runInContext(helperSource, context);

test('existing task tags append without duplicates', () => {
  assert.equal(context.helpers.withTag('health, home', 'work'), 'health, home, work');
  assert.equal(context.helpers.withTag('health, home', 'HEALTH'), 'health, home');
  assert.equal(context.helpers.withTag('', 'personal'), 'personal');
});

test('blank template selection resets all create-form fields', () => {
  assert.match(source, /const templateId = event\.target\.value;[\s\S]*resetCreateForm\(\);[\s\S]*if \(!template\)/);
  assert.match(source, /function resetCreateForm\(\) \{[\s\S]*createForm\.reset\(\);[\s\S]*task-reminder-list/);
});
