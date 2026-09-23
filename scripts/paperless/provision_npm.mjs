// Run inside NPM as its local administrator after a database checkpoint.
import Access from '/app/lib/access.js';
import Model from '/app/models/proxy_host.js';
import Hosts from '/app/internal/proxy-host.js';
const domain='paperless.elliottrook.com';
const existing=await Model.query().where('is_deleted',0);
if(existing.some(x=>x.domain_names.includes(domain)))throw Error('Host exists; inspect instead');
const template=existing.find(x=>x.id===24);
if(!template || template.certificate_id!==8 || !template.advanced_config.includes('auth_request'))throw Error('Template drift');
const fields=['forward_scheme','certificate_id','ssl_forced','caching_enabled','block_exploits','allow_websocket_upgrade','http2_support','hsts_enabled','hsts_subdomains','access_list_id','locations','trust_forwarded_proto'];
const data=Object.fromEntries(fields.filter(k=>template[k]!==undefined).map(k=>[k,template[k]]));
Object.assign(data,{domain_names:[domain],forward_host:'192.168.70.15',forward_port:8000,enabled:true,meta:{},advanced_config:'\n# Private management clients only; public/tunnel requests are denied.\nif ($remote_addr !~ "^192\\.168\\.1\\.(206|241|112)$") { return 403; }\nclient_max_body_size 100m;\n'+template.advanced_config.replaceAll('netbox.elliottrook.com',domain)});
const access=new Access();await access.load(true);
try {const result=await Hosts.create(access,data);console.log(JSON.stringify({id:result.id,domain,certificate_id:result.certificate_id,enabled:result.enabled,nginx_online:result.meta.nginx_online}));process.exit(result.enabled?0:1);}catch{console.error('Paperless proxy creation failed; inspect source-locally');process.exit(1);}
