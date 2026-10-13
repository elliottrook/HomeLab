/** Render one already-provisioned NPM proxy host through NPM's own generator. */

import proxyHostModel from "/app/models/proxy_host.js";
import internalNginx from "/app/internal/nginx.js";

const domain = process.argv[2];
if (!domain) {
  throw new Error("usage: node render_npm_host.mjs <domain>");
}

const host = await proxyHostModel
  .query()
  .findOne({ is_deleted: 0 })
  .whereRaw("domain_names = ?", [JSON.stringify([domain])])
  .withGraphFetched("[owner,certificate,access_list.[clients,items]]");

if (!host) {
  throw new Error(`active proxy host not found: ${domain}`);
}

const meta = await internalNginx.configure(proxyHostModel, "proxy_host", host);
console.log(JSON.stringify({ id: host.id, domain, meta }));
process.exit(meta.nginx_online ? 0 : 1);
