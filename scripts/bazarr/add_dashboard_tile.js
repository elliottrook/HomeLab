// Run inside Homepage. Dry-run unless --apply is present.
const fs = require('fs');
const yaml = require('/app/node_modules/.pnpm/js-yaml@4.1.1/node_modules/js-yaml');
const path = '/app/config/services.yaml';
const original = fs.readFileSync(path, 'utf8');
const before = yaml.load(original);
if (before.some(g => Object.values(g).some(items => items.some(item => 'Bazarr' in item)))) {
  throw Error('Tile exists; inspect instead of duplicating');
}
const anchor = /^- Media Automation:\s*$/m;
if (!anchor.test(original)) throw Error('Expected Media Automation group absent');
const tile = '\n    - Bazarr:\n        icon: bazarr.png\n        href: https://bazarr.elliottrook.com\n        description: Regular and forced subtitle automation';
const candidate = original.replace(anchor, match => match + tile);
const after = yaml.load(candidate);
const group = after.find(g => g['Media Automation'])['Media Automation'];
const added = group.shift();
if (JSON.stringify(after) !== JSON.stringify(before)) throw Error('Unexpected changes');
console.log(JSON.stringify({ tile: added, group: 'Media Automation', mode: process.argv.includes('--apply') ? 'apply' : 'dry-run' }));
if (process.argv.includes('--apply')) {
  const backup = path + '.before-bazarr-' + Date.now();
  fs.writeFileSync(backup, original, { flag: 'wx', mode: 0o600 });
  const stat = fs.statSync(path), temporary = path + '.bazarr-candidate';
  fs.writeFileSync(temporary, candidate, { flag: 'wx', mode: stat.mode & 0o777 });
  fs.chownSync(temporary, stat.uid, stat.gid);
  fs.renameSync(temporary, path);
  console.log(JSON.stringify({ backup, homepage_restart_pending: true }));
}
