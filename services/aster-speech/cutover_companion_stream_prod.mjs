/** Switch only Companion AVS1 streaming between accepted lab and production. */

import proxyHostModel from "/app/models/proxy_host.js";
import internalNginx from "/app/internal/nginx.js";

const apply = process.argv.includes("--apply");
const rollback = process.argv.includes("--rollback");
if (rollback && !apply) throw new Error("--rollback requires --apply");

const domain = "aster.elliottrook.com";
const path = "/voice/v2/";
const labHost = "192.168.70.14";
const prodHost = "192.168.20.37";
const expected = {
  path,
  forward_scheme: "http",
  forward_host: rollback ? prodHost : labHost,
  forward_port: 9131,
  forward_path: "/v2/",
  advanced_config: 'proxy_set_header Connection "close"; proxy_buffering off;',
};
const replacement = {...expected, forward_host: rollback ? labHost : prodHost};

let host = await proxyHostModel.query().findOne({is_deleted: 0})
  .whereRaw("domain_names = ?", [JSON.stringify([domain])]);
if (!host || host.id !== 18 || !host.enabled) throw new Error("Aster proxy host drift");
const locations = host.locations || [];
const indexes = locations.map((location, index) => location.path === path ? index : -1)
  .filter(index => index >= 0);
if (indexes.length !== 1) throw new Error("expected one Companion streaming location");
const index = indexes[0];
const current = locations[index];
if (JSON.stringify(current) !== JSON.stringify(expected)) {
  if (JSON.stringify(current) === JSON.stringify(replacement)) {
    console.log(JSON.stringify({mode: "already-selected", host_id: host.id,
      target: current.forward_host, rollback}));
    process.exit(0);
  }
  throw new Error("Companion streaming location drift");
}
const candidate = locations.map((location, locationIndex) =>
  locationIndex === index ? replacement : location);
console.log(JSON.stringify({mode: apply ? "apply" : "dry-run", host_id: host.id,
  from: current.forward_host, to: replacement.forward_host, rollback}));
if (!apply) process.exit(0);

await proxyHostModel.query().patchAndFetchById(host.id, {locations: candidate});
host = await proxyHostModel.query().findById(host.id)
  .withGraphFetched("[owner,certificate,access_list.[clients,items]]");
const meta = await internalNginx.configure(proxyHostModel, "proxy_host", host);
console.log(JSON.stringify({host_id: host.id, target: replacement.forward_host,
  nginx_online: meta.nginx_online, nginx_err: meta.nginx_err || null}));
process.exit(meta.nginx_online ? 0 : 1);
