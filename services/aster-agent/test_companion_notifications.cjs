const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
function worker() {
  const handlers = {}, shown = [], opened = [];
  const self = {addEventListener: (key, fn) => handlers[key] = fn,
    registration: {showNotification: async (title, value) => shown.push({title, ...value})},
    clients: {matchAll: async()=>[], openWindow: async path=>opened.push(path)}};
  vm.runInNewContext(fs.readFileSync(__dirname+'/static/companion-sw.js','utf8'), {self, URL});
  return {handlers,shown,opened};
}
test('push never displays supplied private text or navigates to supplied URLs', async()=> {
  const f = worker(); let done;
  f.handlers.push({data: {json:()=>({kind:'reply',body:'SECRET',url:'https://evil.invalid',id:'a'.repeat(32)})},waitUntil:p=>done=p});
  await done;
  assert.equal(f.shown[0].body,'Your reply is ready. Open Aster Companion to read it.');
  assert.equal(f.shown[0].data.url,'/companion');
  f.handlers.notificationclick({notification:{close(){},data:{url:'https://evil.invalid'}},waitUntil:p=>done=p});
  await done; assert.deepEqual(f.opened,['/companion']);
});
test('malformed push still produces a generic visible alert with a bounded tag', async()=> {
  const f=worker(); let done;
  f.handlers.push({data:{json:()=>{throw Error('malformed')}},waitUntil:p=>done=p});
  await done; assert.equal(f.shown[0].tag,'aster-update');
  assert.equal(f.shown[0].body,'An update is available in Aster Companion.');
});
function browser() {
  const elements=[], values=new Map(), requests=[];
  let revoked=false;
  const sub={endpoint:'https://web.push.apple.com/synthetic', toJSON:()=>({endpoint:'https://web.push.apple.com/synthetic',expirationTime:null,keys:{p256dh:'synthetic',auth:'synthetic'}}),unsubscribe:async()=>{revoked=true;return true}};
  const registration={pushManager:{getSubscription:async()=>null,subscribe:async()=>sub}};
  const context={URL,Uint8Array,AbortSignal,atob,setTimeout,Date,crypto:require('node:crypto').webcrypto,
    localStorage:{getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)},
    document:{createElement:tag=>{const e={tag,textContent:'',append(){}};elements.push(e);return e},querySelector:()=>({append(){}})},
    navigator:{serviceWorker:{register:async()=>registration,ready:Promise.resolve(registration),getRegistration:async()=>registration}},
    Notification:{permission:'default',requestPermission:async()=>{context.Notification.permission='granted';return 'granted'}},
    PushManager:function(){},validAccessToken:async()=> 'synthetic-token',
    fetch:async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>url.endsWith('/notifications')?{public_key:'AQID',health:{status:'healthy'}}:url.endsWith('/lab-health')?{status:'healthy',checks:[]}:{id:'synthetic-id'}}}};
  context.window=context;
  vm.runInNewContext(fs.readFileSync(__dirname+'/static/companion-notifications.js','utf8'),context);
  return {context,elements,values,requests,registration,sub,revoked:()=>revoked};
}
test('browser subscriptions omit platform metadata from the strict server schema',async()=>{
  const f=browser(); await f.context.companionNotify.init();
  await f.elements.find(e=>e.textContent==='Enable notifications').onclick();
  const request=f.requests.find(r=>r.url.endsWith('/subscriptions'));
  const body=JSON.parse(request.options.body);
  assert.deepEqual(Object.keys(body).sort(),['endpoint','keys']);
  assert.equal(f.values.get('aster_push_subscription'),'synthetic-id');
});
test('expired session does not prevent browser revocation or local sign-out cleanup',async()=>{
  const f=browser(); await f.context.companionNotify.init();
  f.values.set('aster_push_subscription','synthetic-id');
  f.registration.pushManager.getSubscription=async()=>f.sub;
  f.context.validAccessToken=async()=>null;
  await f.context.companionNotify.disable();
  assert.ok(f.revoked()); assert.equal(f.values.has('aster_push_subscription'),false);
});
