// Run inside NPM after checkpointing its database and configuring native OIDC.
import Access from '/app/lib/access.js';
import Model from '/app/models/proxy_host.js';
import Hosts from '/app/internal/proxy-host.js';
const row = await Model.query().findById(25);
if (!row || JSON.stringify(row.domain_names) !== '["paperless.elliottrook.com"]' || row.forward_host !== '192.168.70.15') throw Error('Host identity drift');
if (!row.advanced_config.includes('auth_request /outpost.goauthentik.io/auth/nginx;')) throw Error('Expected old forward-auth configuration');
const boundary = row.advanced_config.indexOf('# Authentik minimal forward-auth gate');
if (boundary < 0) throw Error('Configuration drift');
const advanced_config = row.advanced_config.slice(0, boundary) + `
# Paperless validates Authentik OIDC itself. Never trust caller identity headers.
location / {
    proxy_pass $forward_scheme://$server:$port;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Authentik-Username "";
    proxy_set_header Remote-User "";
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $http_connection;
    proxy_http_version 1.1;
}
`;
const access = new Access(); await access.load(true);
const result = await Hosts.update(access, {id:25, advanced_config});
console.log(JSON.stringify({id:25, oidc:true, nginx_online:result.meta.nginx_online}));
process.exit(result.meta.nginx_online ? 0 : 1);
