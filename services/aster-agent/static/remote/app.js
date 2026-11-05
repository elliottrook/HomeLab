'use strict';
const $ = value => document.querySelector(value);
const errorBox = $('#error');
let rooms = [], selectedRoom = '', statusTimer = null, recorder = null, mediaStream = null;
let inputRevision = '', inputDirty = false;
if (location.search || location.hash) history.replaceState({}, '', '/remote/');

function searchText(value) {
  return value.trim().replace(/[.!?,;:]+$/u, '').trim();
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(path, {...options, headers});
  let result = null;
  if (response.status !== 204) result = await response.json().catch(() => ({}));
  if (response.status === 403) throw new Error('Aster Remote is available only on an authorized home network.');
  if (!response.ok) throw new Error(result?.detail || 'Aster Remote is unavailable.');
  return result;
}
function requestId() { return 'remote-' + crypto.randomUUID().replaceAll('-', '').slice(0, 24); }
function room() { return selectedRoom || $('#room').value; }

async function send(action, text = null) {
  errorBox.textContent = '';
  const body = {request_id: requestId(), room_id: room(), action};
  if (text !== null) body.text = text;
  try { await api('/v1/remote/command', {method: 'POST', body: JSON.stringify(body)}); }
  catch (error) { errorBox.textContent = error.message; }
}
function renderSession(session) {
  rooms = session.rooms || [];
  const select = $('#room'), prior = selectedRoom || select.value;
  select.replaceChildren(...rooms.map(item => {
    const option = document.createElement('option'); option.value = item.room_id; option.textContent = item.label; return option;
  }));
  selectedRoom = rooms.some(item => item.room_id === prior) ? prior : (rooms[0]?.room_id || '');
  select.value = selectedRoom;
  const active = rooms.find(item => item.room_id === selectedRoom);
  $('#roomLabel').textContent = active?.label || 'No AsterTV assigned';
  const connection = $('#connection');
  connection.className = 'status ' + (active?.connected ? 'connected' : 'disconnected');
  connection.setAttribute('aria-label', active?.connected ? 'Connected' : 'Disconnected');
  const input = active?.input || {active:false, sensitive:false, title:'', value:''};
  const field = $('#text'), revision = `${selectedRoom}:${input.active}:${input.sensitive}:${input.title}:${input.value}`;
  $('#textForm').hidden = !input.active;
  $('#keyboardIdle').hidden = input.active;
  if (input.active) {
    $('#textLabel').textContent = input.sensitive ? 'Private Kodi field' : (input.title || 'Kodi text field');
    field.disabled = input.sensitive;
    field.placeholder = input.sensitive ? 'Use the television keyboard for private text' : 'Edit the current text';
    if (!inputDirty && revision !== inputRevision) field.value = input.sensitive ? '' : input.value;
  }
  inputRevision = revision;
}
async function refresh() {
  try { renderSession(await api('/v1/remote/session')); }
  catch (error) { errorBox.textContent = error.message; }
}

document.addEventListener('click', event => {
  const control = event.target.closest('[data-action]');
  if (control && !control.disabled) send(control.dataset.action);
});
$('#room').addEventListener('change', event => {
  selectedRoom = event.target.value; inputDirty = false; inputRevision = ''; refresh();
});
const moreSheet = $('#moreSheet'), moreOpen = $('#moreOpen');
function setMore(open) {
  moreSheet.hidden = !open;
  moreOpen.setAttribute('aria-expanded', String(open));
  if (open) $('#moreClose').focus(); else moreOpen.focus();
}
moreOpen.addEventListener('click', () => setMore(true));
$('#moreClose').addEventListener('click', () => setMore(false));
$('#searchForm').addEventListener('submit', event => {
  event.preventDefault(); const value = searchText($('#search').value);
  if (value) { $('#search').value = value; send('search.open', value); }
});
$('#textForm').addEventListener('submit', event => {
  event.preventDefault(); const value = $('#text').value;
  send('text.replace', value); inputDirty = false;
});
$('#text').addEventListener('input', () => { inputDirty = true; });

const touchpad = $('#touchpad');
let gesture = null;
touchpad.addEventListener('pointerdown', event => {
  gesture = {x: event.clientX, y: event.clientY, time: performance.now()};
  touchpad.setPointerCapture(event.pointerId);
});
touchpad.addEventListener('pointerup', event => {
  if (!gesture) return;
  const dx = event.clientX - gesture.x, dy = event.clientY - gesture.y;
  const duration = performance.now() - gesture.time; gesture = null;
  if (Math.max(Math.abs(dx), Math.abs(dy)) > 38) {
    send(Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'nav.right' : 'nav.left') : (dy > 0 ? 'nav.down' : 'nav.up'));
  } else send(duration > 650 ? 'nav.context' : 'nav.select');
});
touchpad.addEventListener('keydown', event => {
  const actions = {ArrowUp:'nav.up', ArrowDown:'nav.down', ArrowLeft:'nav.left', ArrowRight:'nav.right', Enter:'nav.select', ' ':'nav.select'};
  if (actions[event.key]) { event.preventDefault(); send(actions[event.key]); }
});

async function voiceSearch() {
  if (recorder?.state === 'recording') { recorder.stop(); return; }
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') throw new Error('Voice search is unavailable in this browser.');
  mediaStream = await navigator.mediaDevices.getUserMedia({audio: true});
  const mimeType = ['audio/mp4', 'audio/webm;codecs=opus', 'audio/webm'].find(type => MediaRecorder.isTypeSupported(type));
  recorder = new MediaRecorder(mediaStream, mimeType ? {mimeType} : {});
  const chunks = [];
  recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
  recorder.onstop = async () => {
    $('#voice').classList.remove('recording'); mediaStream?.getTracks().forEach(track => track.stop());
    try {
      const blob = new Blob(chunks, {type: recorder.mimeType || 'audio/mp4'});
      if (!blob.size) throw new Error('No audio was recorded.');
      const form = new FormData(); form.append('audio', blob, blob.type.includes('mp4') ? 'voice.m4a' : 'voice.webm');
      form.append('profile', 'en-GB-media');
      const response = await fetch('/v1/remote/voice', {method:'POST', body:form});
      const result = await response.json();
      if (!response.ok || !result.text?.trim()) throw new Error(result.detail || 'No speech was recognized.');
      const heard = searchText(result.text); if (!heard) throw new Error('No searchable speech was recognized.');
      $('#search').value = heard; $('#search').focus();
      $('#heard').textContent = `Heard: “${heard}” · edit if needed, then search`;
      setTimeout(() => { $('#heard').textContent = ''; }, 8000);
    } catch (error) { errorBox.textContent = error.message; }
    finally { recorder = null; mediaStream = null; }
  };
  recorder.start(); $('#voice').classList.add('recording'); $('#heard').textContent = 'Listening… tap again to search';
  setTimeout(() => { if (recorder?.state === 'recording') recorder.stop(); }, 15000);
}
$('#voice').addEventListener('click', () => voiceSearch().catch(error => { errorBox.textContent = error.message; }));

(async () => {
  if ('serviceWorker' in navigator) {
    let reloading = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (!reloading) { reloading = true; location.replace('/remote/'); }
    });
    navigator.serviceWorker.register('/remote/sw.js', {scope:'/remote/'}).catch(() => {});
  }
  await refresh(); statusTimer = setInterval(refresh, 4000);
})();
