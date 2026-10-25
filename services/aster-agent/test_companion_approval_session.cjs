// Run with node. Exercise the passkey session continuation with inert stubs.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(process.argv[2] || __dirname + '/aster_agent.py', 'utf8');
const start = source.indexOf('async function resumeApprovalAction()');
const end = source.indexOf("document.querySelector('#checkApprovals').onclick", start);
assert.ok(start >= 0 && end > start);
const resume = source.slice(start, end).replaceAll('{{', '{').replaceAll('}}', '}');

const storage = new Map();
const inbox = {textContent: ''};
let loads = 0, managementEffects = 0, brokerEffects = 0;
const ctx = {
  Date,
  JSON,
  localStorage: {
    getItem: key => storage.get(key) ?? null,
    removeItem: key => storage.delete(key),
  },
  document: {querySelector: () => inbox},
  loadManagement: async () => { loads += 1 },
  finishManagementAction: async () => { managementEffects += 1 },
  finishBrokerAction: async () => { brokerEffects += 1 },
};
vm.createContext(ctx);
vm.runInContext(resume, ctx);

function queue(value) {
  storage.set('pending_approval_action', JSON.stringify(value));
  storage.set('pending_approval_created_at', String(Date.now()));
}

(async () => {
  queue({kind: 'session_check'});
  await ctx.resumeApprovalAction();
  assert.equal(loads, 1);
  assert.equal(managementEffects, 0);
  assert.equal(brokerEffects, 0);
  assert.equal(storage.has('pending_approval_action'), false);

  queue({kind: 'unexpected', request_id: 'must-not-run', action: 'approve'});
  await ctx.resumeApprovalAction();
  assert.equal(loads, 1);
  assert.equal(managementEffects, 0);
  assert.equal(brokerEffects, 0);
  assert.match(inbox.textContent, /Unknown pending approval action/);

  assert.match(source, /verifySession\.onclick=\(\)=>login\(true,\{\{kind:'session_check'\}\}\)/);
  assert.match(source, /login\(true,\{\{kind:'broker',request_id:item\.request_id,payload_hash:item\.payload_hash,action:'approve'\}\}\)/);
  console.log('PASS: passkey session continuation is read-only and unknown continuation kinds fail closed');
})().catch(error => { console.error(error); process.exitCode = 1 });
