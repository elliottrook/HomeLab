from datetime import timezone
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import network_diagnostics as network
from test_home_freshness import NOW

HEADER='Iface Destination Gateway Flags RefCnt Use Metric Mask MTU Window IRTT\n'
ROUTE=HEADER+'eth0 00000000 0101A8C0 0003 0 0 100 00000000 0 0 0\n'
ADDR='2: eth0 inet 192.168.1.140/24 brd 192.168.1.255 scope global eth0\n'
DNS='search PRIVATE.internal\nnameserver 192.168.1.1\nnameserver 2606:4700:4700::1111\n'


class NetworkTests(unittest.TestCase):
    def view(self,addr=ADDR,route=ROUTE,dns=DNS,links=None):
        return network.model(addr,route,dns,links or {'eth0':'up'},NOW)

    def test_local_configuration_never_claims_reachability(self):
        view=self.view()
        self.assertEqual(view.state,'Local configuration available')
        self.assertEqual(view.gateway,'192.168.1.1')
        self.assertEqual(view.addresses,(('eth0','192.168.1.140/24'),))
        self.assertEqual(len(view.dns),2);self.assertEqual(view.reachability,'Not tested')
        self.assertNotIn('PRIVATE',repr(view));self.assertNotIn('192.168',repr(view))

    def test_offline_and_missing_configuration_remain_useful(self):
        self.assertEqual(self.view(addr='',route=HEADER,dns='').state,'No local IPv4 address')
        self.assertEqual(self.view(route=HEADER).state,'No default route')
        self.assertEqual(self.view(links={'eth0':'down'}).state,'Link down')
        self.assertEqual(self.view(links={'eth0':'unknown'}).state,'Link state unknown')
        view=self.view(addr=None,route=None,dns=None)
        self.assertEqual(view.state,'No local IPv4 address');self.assertEqual(len(view.notes),5)

    def test_multiple_default_routes_use_metric_and_report_equal_priority(self):
        second='wlan0 00000000 0102A8C0 0003 0 0 200 00000000 0 0 0\n'
        self.assertEqual(self.view(route=ROUTE+second).interface,'eth0')
        view=self.view(route=ROUTE+second.replace('200','100'))
        self.assertEqual(view.state,'Route ambiguous');self.assertIsNone(view.gateway)

    def test_down_routes_ignored_and_onlink_default_is_explicit(self):
        self.assertEqual(self.view(route=ROUTE.replace('0003','0002')).state,'No default route')
        view=self.view(route=ROUTE.replace('0101A8C0','00000000'))
        self.assertIsNone(view.gateway);self.assertIn('on-link',' '.join(view.notes))

    def test_route_without_matching_address_and_link_local_are_not_online(self):
        self.assertEqual(self.view(addr=ADDR.replace('eth0','wlan0')).state,'Default interface has no IPv4 address')
        self.assertEqual(self.view(addr=ADDR.replace('192.168.1.140','169.254.1.5')).state,'Link-local address only')

    def test_addresses_validate_interface_and_skip_loopback(self):
        ips,bad=network.addresses(ADDR+'1: lo inet 127.0.0.1/8 scope host lo\n')
        self.assertEqual(len(ips),1);self.assertFalse(bad)
        for value in (ADDR.replace('eth0','../../config'),ADDR.replace('/24','/99'),
                      ADDR.replace('192.168.1.140','224.1.1.1'),'not an address'):
            self.assertEqual(network.addresses(value),((),True))

    def test_invalid_route_fields_are_not_rendered(self):
        for value in (ROUTE.replace('0101A8C0','PRIVATE'),ROUTE.replace('100','-1'),
                      ROUTE.replace('eth0','../secrets'),'PRIVATE header\n'):
            rows,bad=network.routes(value);self.assertFalse(rows);self.assertTrue(bad)
        self.assertNotIn('PRIVATE',repr(self.view(route='PRIVATE')))

    def test_dns_ignores_domains_and_rejects_non_address_inputs(self):
        values,bad=network.dns_servers(DNS+'nameserver fe80::1%eth0 # local\n')
        self.assertEqual(values[-1],'fe80::1%eth0');self.assertFalse(bad)
        for raw in ('nameserver token.example','nameserver 0.0.0.0','nameserver 224.1.1.1',
                    'nameserver https://secret/','nameserver fe80::1%../../secret'):
            self.assertEqual(network.dns_servers(raw),((),True))

    def test_bounds_and_unknown_link_values(self):
        for parser in (network.addresses,network.routes,network.dns_servers):
            self.assertEqual(parser('x'*65537),((),True))
        view=self.view(links={'eth0':'PRIVATE'})
        self.assertEqual(view.link,'unknown');self.assertNotIn('PRIVATE',repr(view))
        with self.assertRaises(ValueError):network.model(ADDR,ROUTE,DNS,{},NOW.replace(tzinfo=None))

    def test_collector_only_uses_local_read_paths_and_fixed_kernel_command(self):
        paths=[]
        def read(path):
            paths.append(str(path))
            return {'/proc/net/route':ROUTE,'/etc/resolv.conf':DNS,'/sys/class/net/eth0/operstate':'up\n'}.get(str(path))
        result=subprocess.CompletedProcess(['ip'],0,stdout=ADDR.encode())
        with patch.object(network,'read_local',side_effect=read), \
             patch.object(network.subprocess,'run',return_value=result) as run:
            view=network.collect()
        self.assertEqual(set(paths),{'/proc/net/route','/etc/resolv.conf','/sys/class/net/eth0/operstate'})
        self.assertEqual(run.call_args.args[0],['ip','-o','-4','addr','show'])
        self.assertEqual(run.call_args.kwargs['timeout'],3)
        self.assertEqual(view.state,'Local configuration available')

    def test_collector_timeout_does_not_require_the_network(self):
        with patch.object(network,'read_local',return_value=None), \
             patch.object(network.subprocess,'run',side_effect=subprocess.TimeoutExpired('ip',3)):
            view=network.collect()
        self.assertEqual(view.state,'No local IPv4 address');self.assertEqual(view.reachability,'Not tested')


if __name__=='__main__':unittest.main()
