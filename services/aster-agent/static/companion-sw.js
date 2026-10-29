/* No caches, bearer tokens or chat content are stored by this worker. */
self.addEventListener('push', event => {
  let payload = {};
  try { payload = event.data.json(); } catch (_) {}
  const bodies = {
    reply: 'Your reply is ready. Open AsterAI to read it.',
    lab: 'Your lab needs attention. Open AsterAI to review it.',
    test: 'Notifications are connected to AsterAI.'
  };
  const body = bodies[payload.kind] || 'An update is available in AsterAI.';
  const tag = /^[a-f0-9]{32}$/.test(payload.id || '') ? payload.id : 'aster-update';
  // Web Push requires a visible notification. Do not silently discard a push
  // merely because a window is visible: Safari may revoke that permission.
  event.waitUntil(self.registration.showNotification('AsterAI', {
    body, tag, icon: '/companion/orb.png', data: {url: '/companion'},
  }));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({type: 'window', includeUncontrolled: true});
    const client = windows.find(w => new URL(w.url).pathname === '/companion');
    if (client) { await client.focus(); client.postMessage({type: 'aster-notification'}); }
    else await self.clients.openWindow('/companion');
  })());
});
