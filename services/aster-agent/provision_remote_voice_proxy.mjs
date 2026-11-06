/** Add only Mac-backed /voice/v3/ for Aster Remote STT.
 *
 * Run inside the nginx-proxy-manager container. Dry-run is the default;
 * --apply updates the model and uses NPM's validated renderer/reloader.
 * A consistent SQLite checkpoint is mandatory before --apply.
 */

import proxyHostModel from "/app/models/proxy_host.js";
import internalNginx from "/app/internal/nginx.js";

const apply = process.argv.includes("--apply") || process.env.ASTER_APPLY === "1";
const domain = "aster.elliottrook.com";
const canonical = {
  path: "/voice/v3/", forward_scheme: "http", forward_host: "192.168.20.37",
  forward_port: 9131, forward_path: "/",
  advanced_config: 'proxy_set_header Connection "close";',
};
const streaming = {
  path: "/voice/v2/", forward_scheme: "http", forward_host: "192.168.20.37",
  forward_port: 9131, forward_path: "/v2/",
  advanced_config: 'proxy_set_header Connection "close"; proxy_buffering off;',
};
const legacy = {
  path: "/voice/", forward_scheme: "http", forward_host: "192.168.70.14",
  forward_port: 9130, forward_path: "/",
  advanced_config: 'proxy_set_header Connection "close";',
};

let host = await proxyHostModel.query().findOne({is_deleted: 0})
  .whereRaw("domain_names = ?", [JSON.stringify([domain])]);
if (!host || host.id !== 18 || !host.enabled) throw new Error("Aster proxy host drift");
if (host.forward_host !== "192.168.70.10" || host.forward_port !== 9120) {
  throw new Error("Aster default upstream drift");
}
const locations = host.locations || [];
const exact = location => JSON.stringify(location);
if (locations.filter(location => exact(location) === exact(streaming)).length !== 1
    || locations.filter(location => exact(location) === exact(legacy)).length !== 1) {
  throw new Error("accepted voice predecessor drift");
}
const existing = locations.filter(location => location.path === canonical.path);
if (existing.length > 1
    || (existing.length === 1 && exact(existing[0]) !== exact(canonical))) {
  throw new Error("unexpected /voice/v3/ location");
}
const candidate = existing.length ? locations : [canonical, ...locations];
console.log(JSON.stringify({mode: apply ? "apply" : "dry-run", host_id: host.id,
                            locations: candidate}));
if (!apply || existing.length === 1) process.exit(0);

await proxyHostModel.query().patchAndFetchById(host.id, {locations: candidate});
host = await proxyHostModel.query().findById(host.id)
  .withGraphFetched("[owner,certificate,access_list.[clients,items]]");
const meta = await internalNginx.configure(proxyHostModel, "proxy_host", host);
console.log(JSON.stringify({host_id: host.id, nginx_online: meta.nginx_online,
                            nginx_err: meta.nginx_err || null}));
process.exit(meta.nginx_online ? 0 : 1);
