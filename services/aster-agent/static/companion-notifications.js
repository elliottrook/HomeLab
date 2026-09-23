/* Auth is always obtained from the existing Companion session, never the worker. */
window.companionNotify = (() => {
  const sidKey = 'aster_push_subscription';
  const optOutKey = 'aster_push_opt_out';
  const jobKey = 'aster_pending_reply';
  let registration;
  let status;
  const pending = () => { try { return JSON.parse(localStorage.getItem(jobKey)); } catch (_) { return null; } };
  const clearPending = () => localStorage.removeItem(jobKey);
  const enabled = () => Boolean(localStorage.getItem(sidKey)) && localStorage.getItem(optOutKey) !== 'true' && window.Notification?.permission === 'granted';
  async function api(path, options = {}) {
    const token = await validAccessToken();
    if (!token) throw new Error('Sign in to manage notifications or recover your reply.');
    const response = await fetch('/v1/companion/' + path, {
      ...options, headers: {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
      signal: AbortSignal.timeout(15000)
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = result.detail;
      const message = typeof detail === 'string' ? detail : Array.isArray(detail)
        ? detail.map(item => typeof item.msg === 'string' ? item.msg : 'Invalid request').join('; ')
        : 'Notification service is unavailable.';
      throw new Error(message + ' (HTTP ' + response.status + ')');
    }
    return result;
  }
  async function disable() {
    localStorage.setItem(optOutKey, 'true');
    const sid = localStorage.getItem(sidKey);
    let serverRemoved = !sid, browserRemoved = false;
    try {
      const reg = registration || await navigator.serviceWorker?.getRegistration('/companion');
      const sub = await reg?.pushManager.getSubscription();
      browserRemoved = !sub || await sub.unsubscribe();
    } catch (_) {}
    try {
      if (sid) await api('subscriptions/' + encodeURIComponent(sid), {method: 'DELETE'});
      serverRemoved = true;
    } catch (_) {}
    localStorage.removeItem(sidKey);
    // Local logout must work even when the server/session is unavailable.
    if (status) status.textContent = serverRemoved || browserRemoved
      ? 'Notifications are off.' : 'Turn off Aster notifications in Settings; device revocation could not be confirmed.';
  }
  async function enable() {
    // Permission call happens before network awaits, inside the button gesture.
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') throw new Error('Notifications are blocked. Review notification permissions in Settings.');
    const config = await api('notifications');
    const raw = atob(config.public_key.replace(/-/g, '+').replace(/_/g, '/'));
    const key = Uint8Array.from(raw, c => c.charCodeAt(0));
    const subscription = await registration.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: key});
    const saved = await api('subscriptions', {method: 'POST', body: JSON.stringify({endpoint: subscription.endpoint, keys: subscription.toJSON().keys})});
    localStorage.setItem(sidKey, saved.id);
    localStorage.removeItem(optOutKey);
    status.textContent = 'Notifications are on. Previews contain no chat or lab details.';
  }
  async function recover() {
    const job = pending();
    if (!job) return '';
    for (;;) {
      let result;
      try { result = await api('jobs/' + encodeURIComponent(job.id)); }
      catch (error) {
        if (error.message.includes('expired or not found')) clearPending();
        throw error;
      }
      if (result.state === 'done') { clearPending(); return result.result; }
      if (result.state === 'failed') { clearPending(); throw new Error('Aster could not finish this reply. Please send it again.'); }
      if (Date.now() - job.created > 300000) throw new Error('Reply is still pending. Reopen Aster to check it.');
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  async function reply(payload) {
    if (pending()) throw new Error('Reopen Aster to recover your pending reply first.');
    const sid = localStorage.getItem(sidKey);
    const id = crypto.randomUUID().replaceAll('-', '');
    localStorage.setItem(jobKey, JSON.stringify({id, persona: payload.persona, created: Date.now()}));
    await api('jobs?subscription=' + encodeURIComponent(sid) + '&request_id=' + id, {method: 'POST', body: JSON.stringify(payload)});
    return recover();
  }
  async function init() {
    const box = document.createElement('details');
    const heading = document.createElement('summary'); heading.textContent = 'Notifications'; box.append(heading);
    status = document.createElement('p'); box.append(status);
    document.querySelector('#app').append(box);
    if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) {
      status.textContent = 'On iPhone, add Aster to your Home Screen and open it there to enable notifications.'; return;
    }
    try {
      registration = await navigator.serviceWorker.register('/companion/sw.js', {scope: '/companion'});
      await navigator.serviceWorker.ready;
      status.textContent = 'Checking notification settings…';
      for (const [label, action] of [['Enable notifications', enable], ['Disable notifications', disable],
        ['Send test notification', () => api('subscriptions/' + encodeURIComponent(localStorage.getItem(sidKey) || '') + '/test', {method: 'POST'})]]) {
        const button = document.createElement('button'); button.textContent = label;
        button.onclick = async () => { button.disabled = true; try { await action(); } catch (e) { status.textContent = e.message; } finally { button.disabled = false; } };
        box.append(button);
      }
      const config = await api('notifications');
      // Browser permission + PushManager are authoritative. A failed initial
      // server save or missing local ID must not strand a granted subscription.
      const sub = await registration.pushManager.getSubscription();
      if (Notification.permission === 'granted' && sub && localStorage.getItem(optOutKey) !== 'true') {
        const saved = await api('subscriptions', {method: 'POST', body: JSON.stringify({endpoint: sub.endpoint, keys: sub.toJSON().keys})});
        localStorage.setItem(sidKey, saved.id);
      } else {
        localStorage.removeItem(sidKey);
      }
      status.textContent = enabled() ? 'Notifications are on. Previews contain no chat or lab details.'
        : Notification.permission === 'denied' ? 'Notifications are blocked in Settings.' : 'Notifications are off.';
      const health = await api('lab-health');
      const healthStatus = document.createElement('p'); healthStatus.textContent = 'Lab health: ' + health.status; box.append(healthStatus);
      for (const check of health.checks.filter(c => c.status !== 'pass')) {
        const row = document.createElement('p'); row.textContent = check.summary; box.append(row);
      }
      if (config.health.status === 'unavailable') {
        const warning = document.createElement('p'); warning.textContent = 'Lab alerts are paused: the health report needs a fresh update.'; box.append(warning);
      }
    } catch (e) { status.textContent = e.message; }
  }
  return {init, enabled, pending, reply, recover, clearPending, disable};
})();
