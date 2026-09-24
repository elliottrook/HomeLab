"""Append only the private Paperless record to a named local Pi-hole container."""
import json,subprocess,sys,tomllib
container=sys.argv[1]
assert container in ('pihole','ix-pihole-pihole-1')
prefix=['docker','exec',container]
raw=subprocess.check_output(prefix+['cat','/etc/pihole/pihole.toml'])
hosts=tomllib.loads(raw.decode())['dns']['hosts'];record='192.168.50.23 paperless.elliottrook.com'
assert not any('paperless.elliottrook.com' in x for x in hosts)
subprocess.run(prefix+['sh','-c','umask 077; test ! -e /etc/pihole/pihole.toml.before-paperless-20260923; cp /etc/pihole/pihole.toml /etc/pihole/pihole.toml.before-paperless-20260923; chmod 600 /etc/pihole/pihole.toml.before-paperless-20260923'],check=True)
subprocess.run(prefix+['pihole-FTL','--config','dns.hosts',json.dumps(hosts+[record])],check=True,stdout=subprocess.DEVNULL)
subprocess.run(prefix+['pihole','reloaddns'],check=True,stdout=subprocess.DEVNULL)
new=tomllib.loads(subprocess.check_output(prefix+['cat','/etc/pihole/pihole.toml']).decode())['dns']['hosts'];assert new==hosts+[record]
print(json.dumps({'container':container,'added':record,'existing_records_preserved':True}))
