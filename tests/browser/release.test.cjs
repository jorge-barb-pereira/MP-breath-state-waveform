'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { inspect } = require('../../tools/check_laboratory.cjs');
const root = path.resolve(__dirname, '../..');

test('browser entry point enforces offline execution with only local assets', () => {
  const html = fs.readFileSync(path.join(root, 'laboratory/index.html'), 'utf8');
  assert.match(html, /connect-src 'none'/); assert.match(html, /form-action 'none'/);
  assert.doesNotMatch(html, /<input[^>]+type=["']file/i);
  for (const match of html.matchAll(/(?:src|href)="([^"]+)"/g)) {
    if (match[1].startsWith('#')) continue;
    assert.doesNotMatch(match[1], /^(?:https?:|\/\/|data:)/);
    assert.ok(fs.existsSync(path.join(root, 'laboratory', match[1])));
  }
  for (const name of ['laboratory/src/app.js', 'laboratory/src/model.js']) {
    const code = fs.readFileSync(path.join(root, name), 'utf8');
    assert.doesNotMatch(code, /\b(?:fetch|XMLHttpRequest|WebSocket|sendBeacon|localStorage|sessionStorage|indexedDB)\b/);
    assert.doesNotMatch(code, /\b(?:innerHTML|eval)\b|new Function\b/);
  }
});

test('every static page ID is unique and controls have explicit labels', () => {
  const html = fs.readFileSync(path.join(root, 'laboratory/index.html'), 'utf8');
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(ids.length, new Set(ids).size);
  for (const id of ['period', 'expiration', 'pause', 'amplitude', 'bins']) assert.ok(html.includes(`label for="${id}"`));
});

test('release review rejects extra files and sensitive token patterns', () => {
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'breath-release-test-'));
  try {
    fs.writeFileSync(path.join(folder, 'PUBLICATION_ALLOWLIST.txt'), 'PUBLICATION_ALLOWLIST.txt\nsafe.txt\n');
    fs.writeFileSync(path.join(folder, 'safe.txt'), 'Synthetic numerical example.');
    assert.equal(inspect(folder, false).files, 2);
    const extra = path.join(folder, 'unexpected.txt');
    fs.writeFileSync(extra, 'Invented sentinel.');
    assert.throws(() => inspect(folder, false), /Unapproved/); fs.unlinkSync(extra);
    fs.writeFileSync(path.join(folder, 'safe.txt'), 'ghp_' + 'A'.repeat(30));
    assert.throws(() => inspect(folder, false), /Sensitive category/);
  } finally { fs.rmSync(folder, { recursive: true, force: true }); }
});
