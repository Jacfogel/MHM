import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(new URL('./checkin.js', import.meta.url), 'utf8');
const css = await readFile(new URL('./styles.css', import.meta.url), 'utf8');

test('the answer box clears whenever a check-in question is shown', () => {
  assert.match(source, /form\.hidden = !result\.active;\s*answer\.value = '';/);
});

test('scale and yes or no questions offer a one-tap answer', () => {
  assert.match(source, /type === 'scale_1_5'/);
  assert.match(source, /choiceButton\('Yes', 'yes'\)/);
  assert.match(source, /choiceButton\('No', 'no'\)/);
  assert.match(source, /const typed = type !== 'scale_1_5' && type !== 'yes_no' && !sleep/);
  assert.match(source, /Fell asleep/);
  assert.match(source, /Woke up/);
  assert.match(source, /answerField\.hidden = !typed/);
  assert.match(source, /type === 'time_pair'/);
});

test('check-in prompts keep the line break before the next question', () => {
  assert.match(css, /#checkin-message \{ white-space: pre-wrap; \}/);
});
