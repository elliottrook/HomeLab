// Run against the actual JavaScript rendered by companion_web_client.
// Usage: node services/aster-agent/test_companion_voice.cjs /tmp/aster-companion.js
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const script = fs.readFileSync(process.argv[2] || '/tmp/aster-companion.js', 'utf8');
const voice = script.slice(script.indexOf('// A voice turn owns'), script.indexOf("document.querySelector('#mic').onclick"));
function fixture(){
  const elements = new Map();
  const el = id => {
    if(!elements.has(id)) elements.set(id, {hidden:true, textContent:'', disabled:false, classList:{add(){},remove(){}}, play:async()=>{}, pause(){},load(){},removeAttribute(){}});
    return elements.get(id);
  };
  let revoked = 0;
  const context = vm.createContext({document:{querySelector:el}, navigator:{}, prompt:el('#prompt'), orb:el('#orb'), chatBusy:false,
    AbortController, setTimeout, clearTimeout, Blob, FormData,
    URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:()=>revoked++},
    validAccessToken:async()=> 'synthetic-test-token', fetch:async()=> ({ok:true,blob:async()=>new Blob(['test'])})});
  vm.runInContext(voice,context);
  return {context,el,run:s=>vm.runInContext(s,context),revoked:()=>revoked};
}
test('long replies preserve text and stay under the API limit, including emoji',()=>{
 const f=fixture();
 for(const value of ['word '.repeat(2000).trim(), 'x'.repeat(5000), '😀'.repeat(2100)]){
  f.context.input=value;
  const chunks=f.run('speechChunks(input)');
  assert.ok(chunks.every(c=>c.length<=1800 && !/^[\uDC00-\uDFFF]|[\uD800-\uDBFF]$/.test(c)));
  assert.equal(chunks.join(' ').replaceAll(' ',''),value.replaceAll(' ',''));
 }
});
test('autoplay denial retains audio for manual Play, then releases the URL',async()=>{
 const f=fixture();
 f.el('#voiceAudio').play=async()=>{throw Object.assign(new Error('blocked'),{name:'NotAllowedError'})};
 const playing=f.run('playSpeechBlob(new Blob(["test"]))');
 await new Promise(setImmediate);
 assert.match(f.el('#voiceStatus').textContent,/tap Play/);
 assert.equal(f.el('#voiceAudio').hidden,false);
 assert.equal(f.revoked(),0);
 f.el('#voiceAudio').onended();
 assert.equal(await playing,true);
 assert.equal(f.revoked(),1);
 assert.equal(f.el('#voiceAudio').hidden,true);
});
test('decode/playback failures are surfaced and cleaned up',async()=>{
 const f=fixture();
 f.el('#voiceAudio').play=async()=>{throw new Error('decode')};
 await assert.rejects(f.run('playSpeechBlob(new Blob(["test"]))'),/playback failed/);
 assert.equal(f.revoked(),1);
});
test('stop speech releases a manual-play wait and does not synthesize later chunks',async()=>{
 const f=fixture(); let requests=0;
 f.context.fetch=async()=>{requests++;return {ok:true,blob:async()=>new Blob(['test'])}};
 f.el('#voiceAudio').play=async()=>{throw Object.assign(new Error('blocked'),{name:'NotAllowedError'})};
 const speaking=f.run('speakReply("word ".repeat(1000))');
 await new Promise(setImmediate);
 f.el('#stopSpeech').onclick();
 await speaking;
 assert.equal(requests,1);
 assert.equal(f.el('#stopSpeech').hidden,true);
 assert.equal(f.revoked(),1);
});
test('microphone acquisition is serialized and recorder setup failure stops tracks',async()=>{
 const f=fixture();let acquire=0,stop=0,grant;
 f.context.navigator.mediaDevices={getUserMedia:()=>{acquire++;return new Promise(r=>grant=r)}};
 f.context.MediaRecorder=class {static isTypeSupported(){return true} constructor(){throw new Error('recorder setup failed')}};
 const first=f.run('toggleMic()');
 await f.run('toggleMic()');
 assert.equal(acquire,1);
 grant({getTracks:()=>[{stop(){stop++}}]});
 await first;
 assert.equal(stop,1);
 assert.match(f.el('#chatErr').textContent,/setup failed/);
 assert.equal(f.run('voiceBusy'),false);
});
test('server errors preserve actionable authentication status',async()=>{
 const f=fixture();f.context.fetch=async()=>({ok:false,status:401,json:async()=>({detail:'Invalid or missing credentials'})});
 await assert.rejects(f.run('voiceFetch("/voice/v1/stt", {})'),/Invalid or missing credentials/);
});
