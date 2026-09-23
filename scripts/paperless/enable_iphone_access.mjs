// Narrow existing private HTTPS access to include the Tailscale subnet router.
// Run in NPM only after an approved database checkpoint.
import Access from '/app/lib/access.js';
import Model from '/app/models/proxy_host.js';
import Hosts from '/app/internal/proxy-host.js';
const row=await Model.query().findById(25);
if(!row || JSON.stringify(row.domain_names)!=='["paperless.elliottrook.com"]' || row.forward_host!=='192.168.70.15')throw Error('Host identity drift');
const old='if ($remote_addr !~ "^192\\.168\\.1\\.(206|241|112)$") { return 403; }';
const next='if ($remote_addr !~ "^(192\\.168\\.1\\.(206|241|112)|192\\.168\\.20\\.20)$") { return 403; }';
if(!row.advanced_config.includes(old) || !row.advanced_config.includes('auth_request /outpost.goauthentik.io/auth/nginx;'))throw Error('Access configuration drift');
const access=new Access();await access.load(true);
await Hosts.update(access,{id:25,advanced_config:row.advanced_config.replace(old,next).replace('# Private management clients only; public/tunnel requests are denied.','# Approved management clients and Tailscale subnet router only; public requests denied.')});
console.log(JSON.stringify({host_id:25,added_source:'192.168.20.20',iphone_wifi:'192.168.1.112',authentik_preserved:true}));process.exit(0);
