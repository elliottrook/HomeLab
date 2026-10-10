// Run inside NPM after a database checkpoint. Uses the existing Sonarr host
// as the approved forward-auth template and creates only Bazarr's host.
import Access from '/app/lib/access.js';
import Model from '/app/models/proxy_host.js';
import Hosts from '/app/internal/proxy-host.js';

const domain = 'bazarr.elliottrook.com';
const existing = await Model.query().where('is_deleted', 0);
if (existing.some(x => x.domain_names.includes(domain))) throw Error('Host exists; inspect instead');
const template = existing.find(x => x.id === 10);
if (!template || template.certificate_id !== 8 || !template.advanced_config.includes('auth_request')) {
  throw Error('Sonarr forward-auth template drift');
}
const fields = ['forward_scheme', 'certificate_id', 'ssl_forced', 'caching_enabled',
  'block_exploits', 'allow_websocket_upgrade', 'http2_support', 'hsts_enabled',
  'hsts_subdomains', 'access_list_id', 'locations', 'trust_forwarded_proto'];
const data = Object.fromEntries(fields.filter(k => template[k] !== undefined).map(k => [k, template[k]]));
Object.assign(data, {
  domain_names: [domain], forward_host: '192.168.20.40', forward_port: 6767,
  enabled: true, meta: {},
  advanced_config: template.advanced_config.replaceAll('sonarr.elliottrook.com', domain),
});
const access = new Access();
await access.load(true);
const result = await Hosts.create(access, data);
console.log(JSON.stringify({ id: result.id, domain, certificate_id: result.certificate_id,
  enabled: result.enabled, nginx_online: result.meta?.nginx_online }));
process.exit(result.enabled ? 0 : 1);
