import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./script.js', import.meta.url), 'utf8');

function page() {
  const classNames = new Set();
  const listeners = {};
  const windowListeners = {};
  const attrs = { 'aria-expanded': 'false' };
  const toggle = {
    textContent: 'Menu',
    getAttribute(name) { return attrs[name]; },
    setAttribute(name, value) { attrs[name] = value; },
    addEventListener(type, listener) { listeners[`toggle:${type}`] = listener; },
  };
  const menu = {
    classList: {
      toggle(name, force) {
        if (force) classNames.add(name);
        else classNames.delete(name);
      },
      contains(name) { return classNames.has(name); },
    },
    addEventListener(type, listener) { listeners[`menu:${type}`] = listener; },
  };
  vm.runInContext(source, vm.createContext({
    document: {
      getElementById(id) {
        if (id === 'year') return null;
        if (id === 'nav-toggle') return toggle;
        if (id === 'site-menu') return menu;
        return null;
      },
      querySelectorAll() { return []; },
      addEventListener() {},
    },
    window: { addEventListener(type, listener) { windowListeners[type] = listener; } },
  }));
  return { toggle, classNames, listeners, windowListeners };
}

test('nav toggle opens and closes the compact menu', () => {
  const view = page();
  view.listeners['toggle:click']();
  assert.equal(view.toggle.getAttribute('aria-expanded'), 'true');
  assert.equal(view.classNames.has('is-open'), true);
  assert.equal(view.toggle.textContent, 'Close');
  view.listeners['toggle:click']();
  assert.equal(view.toggle.getAttribute('aria-expanded'), 'false');
  assert.equal(view.classNames.has('is-open'), false);
  assert.equal(view.toggle.textContent, 'Menu');
});

test('feature tabs hide when that feature is off and the open page returns home', async () => {
  const links = [
    { dataset: { feature: 'checkins' }, hidden: false, getAttribute() { return null; } },
    { dataset: { feature: 'messages' }, hidden: false, getAttribute() { return 'page'; } },
  ];
  const navigation = [];
  vm.runInContext(source, vm.createContext({
    document: {
      getElementById() { return null; },
      querySelectorAll() { return links; },
      addEventListener() {},
    },
    fetch: async () => ({ ok: true, json: async () => ({ messages_enabled: false, tasks_enabled: false, checkins_enabled: true }) }),
    location: { replace(url) { navigation.push(url); } },
    window: { addEventListener() {} },
  }));
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(links[0].hidden, false);
  assert.equal(links[1].hidden, true);
  assert.deepEqual(navigation, ['home.html']);
});

test('a click outside an open dialog closes it', () => {
  const listeners = {};
  const dialog = {
    open: true,
    closed: false,
    preventClose: false,
    close() { this.closed = true; this.open = false; },
    dispatchEvent(event) {
      if (this.preventClose) event.preventDefault();
      return !event.defaultPrevented;
    },
    getBoundingClientRect() { return { left: 100, top: 100, right: 300, bottom: 400 }; },
  };
  vm.runInContext(source, vm.createContext({
    document: {
      getElementById() { return null; },
      querySelectorAll(selector) { return selector === 'dialog' ? [dialog] : []; },
      addEventListener(type, listener, capture) { listeners[`${type}:${Boolean(capture)}`] = listener; },
    },
    window: { addEventListener() {} },
    Event,
    WeakMap,
  }));
  const outside = { clientX: 10, clientY: 10 };
  const inside = { clientX: 150, clientY: 150 };
  listeners['pointerdown:true'](outside);
  listeners['click:false'](outside);
  assert.equal(dialog.closed, true);

  dialog.open = true;
  dialog.closed = false;
  listeners['pointerdown:true'](inside);
  listeners['click:false'](outside);
  assert.equal(dialog.closed, false);

  listeners['pointerdown:true'](inside);
  listeners['click:false'](inside);
  assert.equal(dialog.closed, false);

  dialog.open = false;
  listeners['pointerdown:true'](outside);
  dialog.open = true;
  listeners['click:false'](outside);
  assert.equal(dialog.closed, false);

  dialog.preventClose = true;
  listeners['pointerdown:true'](outside);
  listeners['click:false'](outside);
  assert.equal(dialog.closed, false);
});

test('escape and choosing a destination close the compact menu', () => {
  const view = page();
  view.listeners['toggle:click']();
  view.windowListeners.keydown({ key: 'Escape' });
  assert.equal(view.toggle.getAttribute('aria-expanded'), 'false');
  view.listeners['toggle:click']();
  view.listeners['menu:click']({ target: { closest(selector) { return selector.includes('a') ? {} : null; } } });
  assert.equal(view.toggle.getAttribute('aria-expanded'), 'false');
  assert.equal(view.classNames.has('is-open'), false);
});
