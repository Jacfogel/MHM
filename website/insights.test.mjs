import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(new URL('./insights.js', import.meta.url), 'utf8');

test('insight range changes ignore stale responses', () => {
  assert.match(source, /const request = \+\+loadRequest/);
  assert.match(source, /requestedDays !== days\.value/);
  assert.match(source, /content\.setAttribute\('aria-busy', 'true'\)/);
  assert.match(source, /content\.removeAttribute\('aria-busy'\)/);
});

test('check-in requests are explicit and single-flight', () => {
  assert.match(source, /if \(checkinRequest\.disabled\) return/);
  assert.match(source, /Queueing your check-in/);
  assert.match(source, /checkinRequest\.setAttribute\('aria-busy', 'true'\)/);
  assert.match(source, /checkinRequest\.removeAttribute\('aria-busy'\)/);
});
