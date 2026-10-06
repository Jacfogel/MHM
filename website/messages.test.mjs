import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(new URL('./messages.js', import.meta.url), 'utf8');
const html = await readFile(new URL('./messages.html', import.meta.url), 'utf8');

test('message category loads ignore stale responses', () => {
  assert.match(source, /const request = \+\+loadRequest/);
  assert.match(source, /if \(request !== loadRequest\) return/);
  assert.match(source, /if \(request === loadRequest\) showStatus/);
});

test('unsaved messages are protected from accidental workflow changes', () => {
  assert.match(source, /form\.dataset\.dirty = 'true'/);
  assert.match(source, /Discard this unsaved message and change categories/);
  assert.match(source, /Discard this unsaved message and edit another one/);
  assert.match(source, /mhm:before-logout/);
  assert.match(source, /beforeunload/);
});

test('category test action is explicit and single-flight', () => {
  assert.match(html, />Send category test</);
  assert.match(source, /if \(testButton\.disabled\) return/);
  assert.match(source, /testButton\.setAttribute\('aria-busy', 'true'\)/);
  assert.match(source, /testButton\.removeAttribute\('aria-busy'\)/);
});
