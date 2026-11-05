'use strict';
const AUTH = {
  clientId: 'aster-companion',
  authorizeUrl: 'https://auth.elliottrook.com/application/o/authorize/',
  tokenUrl: 'https://auth.elliottrook.com/application/o/token/',
  scope: 'openid profile',
  redirectUri: location.origin + '/remote/',
};
const $ = value => document.querySelector(value);
const loginPanel = $('#login'), remotePanel = $('#remote'), errorBox = $('#error');
let rooms = [], selectedRoom = '', statusTimer = null, recorder = null, mediaStream = null;

function b64url(buffer) {
  return btoa(String.fromCharCode(...new Uint8Array(buffer)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function randomString(length) {
  const value = new Uint8Array(length); crypto.getRandomValues(value); return b64url(value);
}
async function sha256(value) {
  return crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
}
function token() { return sessionStorage.getItem('aster_remote_access_token'); }
function clearSession() { sessionStorage.removeItem('aster_remote_access_token'); }

async function login() {
  const verifier = randomString(64), state = randomString(24);
  sessionStorage.setItem('aster_remote_verifier', verifier);
  sessionStorage.setItem('aster_remote_state', state);
  const query = new URLSearchParams({
    client_id: AUTH.clientId, response_type: 'code', redirect_uri: AUTH.redirectUri,
    scope: AUTH.scope, code_challenge: b64url(await sha256(verifier)),
    code_challenge_method: 'S256', state,
  });
  location.href = AUTH.authorizeUrl + '?' + query;
}
async function callback() {
  const query = new URLSearchParams(location.search), code = query.get('code');
  if (!code) return;
  const state = sessionStorage.getItem('aster_remote_state');
  const verifier = sessionStorage.getItem('aster_remote_verifier');
  sessionStorage.removeItem('aster_remote_state');
  sessionStorage.removeItem('aster_remote_verifier');
  history.replaceState({}, '', '/remote/');
  if (!state || query.get('state') !== state || !verifier) throw new Error('Login state did not match.');
  const body = new URLSearchParams({
    grant_type: 'authorization_code', code, redirect_uri: AUTH.redirectUri,
    client_id: AUTH.clientId, code_verifier: verifier,
  });
  const response = await fetch(AUTH.tokenUrl, {
    method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body,
  });
  const result = await response.json();
  if (!response.ok || !result.access_token) throw new Error(result.error_description || 'Login failed.');
  sessionStorage.setItem('aster_remote_access_token', result.access_token);
}
async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set('Authorization', 'Bearer ' + (token() || ''));
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(path, {...options, headers});
  if (response.status === 401) { clearSession(); showLogin(); throw new Error('Session expired. Sign in again.'); }
  let result = null;
  if (response.status !== 204) result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result?.detail || 'Aster Remote is unavailable.');
  return result;
}
function showLogin() { loginPanel.hidden = false; remotePanel.hidden = true; }
function showRemote() { loginPanel.hidden = true; remotePanel.hidden = false; }
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
  const connection = $('#connection');
  connection.textContent = active?.connected ? 'Connected' : 'Disconnected';
  connection.className = 'status ' + (active?.connected ? 'connected' : 'disconnected');
  $('#now').textContent = active ? `${active.current_page} · ${active.playback}` : 'No room is assigned';
}
async function refresh() {
  if (!token()) return;
  try { renderSession(await api('/v1/remote/session')); }
  catch (error) { errorBox.textContent = error.message; }
}

document.addEventListener('click', event => {
  const control = event.target.closest('[data-action]');
  if (control && !control.disabled) send(control.dataset.action);
});
$('#room').addEventListener('change', event => { selectedRoom = event.target.value; refresh(); });
$('#searchForm').addEventListener('submit', event => {
  event.preventDefault(); const value = $('#search').value.trim();
  if (value) { send('search.open', value); $('#search').value = ''; }
});
$('#textForm').addEventListener('submit', event => {
  event.preventDefault(); const value = $('#text').value;
  if (value) { send('text.send', value); $('#text').value = ''; }
});

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
      const response = await fetch('/voice/v1/stt', {method:'POST', headers:{Authorization:'Bearer ' + token()}, body:form});
      const result = await response.json();
      if (!response.ok || !result.text?.trim()) throw new Error(result.detail || 'No speech was recognized.');
      const heard = result.text.trim(); $('#heard').textContent = `Heard: “${heard}”`;
      await send('voice.search', heard);
      setTimeout(() => { $('#heard').textContent = ''; }, 5000);
    } catch (error) { errorBox.textContent = error.message; }
    finally { recorder = null; mediaStream = null; }
  };
  recorder.start(); $('#voice').classList.add('recording'); $('#heard').textContent = 'Listening… tap again to search';
  setTimeout(() => { if (recorder?.state === 'recording') recorder.stop(); }, 15000);
}
$('#voice').addEventListener('click', () => voiceSearch().catch(error => { errorBox.textContent = error.message; }));
$('#signIn').addEventListener('click', () => login().catch(error => { $('#loginError').textContent = error.message; }));
$('#signOut').addEventListener('click', () => { clearSession(); showLogin(); });

(async () => {
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/remote/sw.js', {scope:'/remote/'}).catch(() => {});
  try { await callback(); } catch (error) { $('#loginError').textContent = error.message; }
  if (!token()) { showLogin(); return; }
  showRemote(); await refresh(); statusTimer = setInterval(refresh, 4000);
})();
