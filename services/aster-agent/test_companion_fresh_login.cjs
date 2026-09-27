// Run with node. Execute the served login function with inert browser stubs.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(__dirname + '/aster_agent.py', 'utf8');
const start = source.indexOf('async function login(fresh=');
const end = source.indexOf('function storeTokens(j)', start);
assert.ok(start >= 0 && end > start);
const login = source.slice(start, end).replaceAll('{{', '{').replaceAll('}}', '}');
const handler = source.split('\n').find(s => s.startsWith("document.querySelector('#signin').onclick="));
const button = {};
const session = new Map();
const storage = new Map();
const ctx = {
  AUTH: {clientId:'fixture', redirectUri:'https://fixture.invalid/companion', scope:'openid', authorizeUrl:'https://auth.invalid/authorize'},
  URLSearchParams,
  sessionStorage: {setItem:(k,v)=>session.set(k,v)},
  localStorage: {setItem:(k,v)=>storage.set(k,v)},
  document: {querySelector:()=>button}, location: {},
  randomString:n=>'x'.repeat(n), sha256:async s=>s, b64url:s=>s,
};
vm.createContext(ctx);
vm.runInContext(login + '\n' + handler, ctx);
(async()=>{
  await button.onclick();
  let q = new URL(ctx.location.href).searchParams;
  assert.equal(q.get('prompt'), 'login');
  assert.equal(q.get('max_age'), null);
  assert.equal(q.get('code_challenge_method'), 'S256');
  assert.ok(session.get('pkce_state'));
  assert.equal(storage.size, 0);
  const action = {kind:'management',body:{action:'agent_state',target:'fixture-only',state:'suspended'}};
  await ctx.login(true, action);
  q = new URL(ctx.location.href).searchParams;
  assert.equal(q.get('prompt'), 'login');
  assert.deepEqual(JSON.parse(storage.get('pending_approval_action')), action);
  console.log('PASS: explicit sign-in and privileged reauthentication require prompt=login; PKCE and pending action preserved');
})().catch(e=>{console.error(e);process.exitCode=1});
