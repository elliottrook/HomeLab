/** Add only /voice/v2/ to the existing Aster NPM host.
 *
 * Run inside the nginx-proxy-manager container. Dry-run is the default;
 * --apply updates the model and uses NPM's own validated renderer/reloader.
 * Take a consistent SQLite backup before --apply.
 */

import proxyHostModel from "/app/models/proxy_host.js";
import internalNginx from "/app/internal/nginx.js";

const apply = process.argv.includes("--apply") || process.env.ASTER_APPLY === "1";
const domain = "aster.elliottrook.com";
const legacy = {
  path: "/voice/", forward_scheme: "http", forward_host: "192.168.70.14",
  forward_port: 9130, forward_path: "/",
  advanced_config: 'proxy_set_header Connection "close";',
};
const streaming = {
  path: "/voice/v2/", forward_scheme: "http", forward_host: "192.168.70.14",
  forward_port: 9131, forward_path: "/v2/",
  advanced_config: 'proxy_set_header Connection "close"; proxy_buffering off;',
};

let host = await proxyHostModel.query().findOne({is_deleted: 0})
  .whereRaw("domain_names = ?", [JSON.stringify([domain])]);
if (!host || host.id !== 18 || !host.enabled) throw new Error("Aster proxy host drift");
if (host.forward_host !== "192.168.70.10" || host.forward_port !== 9120) {
  throw new Error("Aster default upstream drift");
}
const locations = host.locations || [];
if (locations.length < 1 || JSON.stringify(locations[locations.length - 1]) !== JSON.stringify(legacy)) {
  throw new Error("legacy /voice/ location drift");
}
const existing = locations.filter(location => location.path === streaming.path);
if (existing.length > 1 || (existing.length === 1 && JSON.stringify(existing[0]) !== JSON.stringify(streaming))) {
  throw new Error("unexpected /voice/v2/ location");
}
const candidate = existing.length ? locations : [streaming, ...locations];
console.log(JSON.stringify({mode: apply ? "apply" : "dry-run", host_id: host.id, locations: candidate}));
if (!apply || existing.length === 1) process.exit(0);

await proxyHostModel.query().patchAndFetchById(host.id, {locations: candidate});
host = await proxyHostModel.query().findById(host.id)
  .withGraphFetched("[owner,certificate,access_list.[clients,items]]");
const meta = await internalNginx.configure(proxyHostModel, "proxy_host", host);
console.log(JSON.stringify({host_id: host.id, nginx_online: meta.nginx_online, nginx_err: meta.nginx_err || null}));
process.exit(meta.nginx_online ? 0 : 1);
