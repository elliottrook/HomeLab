#!/usr/bin/env node
// Render only the two bounded Aster Games NPM hosts.

import internalNginx from "/app/internal/nginx.js";
import proxyHostModel from "/app/models/proxy_host.js";

const expected = new Map([
    [42, "games.elliottrook.com"],
    [43, "romarr.elliottrook.com"],
]);

for (const [id, domain] of expected) {
    const row = await proxyHostModel
        .query()
        .findById(id)
        .allowGraph(proxyHostModel.defaultAllowGraph)
        .withGraphFetched(`[${proxyHostModel.defaultExpand.join(", ")}]`);
    if (!row || row.is_deleted || !row.enabled || row.domain_names.length !== 1 ||
        row.domain_names[0] !== domain) {
        throw new Error(`NPM host identity mismatch for ${id}`);
    }
    const metadata = await internalNginx.configure(proxyHostModel, "proxy_host", row);
    if (!metadata.nginx_online || metadata.nginx_err) {
        throw new Error(`NPM render failed for ${id}`);
    }
    console.log(JSON.stringify({id, domain, nginx_online: true}));
}
