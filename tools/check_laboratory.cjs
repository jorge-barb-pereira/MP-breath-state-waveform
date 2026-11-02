'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const ROOT = path.resolve(__dirname, '..');

function inspect(root = ROOT, checkGit = true) {
  const list = fs.readFileSync(path.join(root, 'PUBLICATION_ALLOWLIST.txt'), 'utf8').trim().split(/\r?\n/);
  const allowed = new Set(list);
  if (allowed.size !== list.length) throw new Error('Duplicate release allowlist entry');
  const found = [];
  function walk(folder) {
    for (const entry of fs.readdirSync(folder, { withFileTypes: true })) {
      const absolute = path.join(folder, entry.name), relative = path.relative(root, absolute).split(path.sep).join('/');
      if (['.git', 'output', 'node_modules', '__pycache__', '.venv', '.test-tmp', '.pytest_cache'].includes(entry.name)) continue;
      if (entry.isSymbolicLink()) throw new Error('Symbolic links are not permitted');
      if (entry.isDirectory()) { walk(absolute); continue; }
      if (!entry.isFile() || !allowed.has(relative)) throw new Error(`Unapproved release path: ${relative}`);
      const raw = fs.readFileSync(absolute);
      if (relative === 'docs/figures/breath-state-functions.png') { found.push(relative); continue; }
      const content = new TextDecoder('utf-8', { fatal: true }).decode(raw);
      const patterns = [
        /(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}/,
        /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/,
        /[A-Za-z]:[\\/]+Users[\\/]/,
        /\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2})\b/
      ];
      if (patterns.some(pattern => pattern.test(content))) throw new Error(`Sensitive category detected in ${relative}`);
      found.push(relative);
    }
  }
  walk(root);
  if (found.length !== allowed.size || list.some(item => !found.includes(item))) throw new Error('Release allowlist does not match the candidate files');
  if (checkGit && fs.existsSync(path.join(root, '.git'))) {
    const tracked = execFileSync('git', ['-C', root, 'ls-files', '-z'], { encoding: 'utf8' }).split('\0').filter(Boolean);
    if (tracked.some(item => !allowed.has(item))) throw new Error('An unapproved file is tracked by Git');
    const historical = execFileSync('git', ['-C', root, 'log', '--all', '--format=', '--name-only'], { encoding: 'utf8' });
    if (historical.split(/\r?\n/).filter(Boolean).some(item => !allowed.has(item))) throw new Error('An unapproved file appears in local Git history');
  }
  return { files: found.length, paths: found.sort() };
}

module.exports = { inspect };
if (require.main === module) {
  try { console.log(`PASS: ${inspect().files} allowlisted files; text patterns and tracked paths/history checked; run Python release check for PNG metadata`); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
