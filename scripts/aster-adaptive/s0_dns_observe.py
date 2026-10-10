"""Fixed synthetic Pi-hole DNS probe. No default live socket factory."""
import struct
import time
from s0_probe_state import QUERY_ID, QUESTION, dns


def denied_socket():raise PermissionError('live DNS disabled pending review')


def collect_stub_dns(*, socket_factory=denied_socket, clock=time.monotonic):
    responses=[]
    query=struct.pack('!6H',QUERY_ID,0x0100,1,0,0,0)+QUESTION
    for _ in range(2):
        sock=socket_factory()
        try:
            sock.settimeout(2);start=clock()
            sock.sendto(query,('192.168.20.20',53))
            packet,peer=sock.recvfrom(513)
            if peer!=('192.168.20.20',53) or len(packet)>512:raise ValueError('DNS peer/size')
            responses.append({'packet_hex':packet.hex(),'elapsed_ms':(clock()-start)*1000})
        finally:sock.close()
    result={'responses':responses};dns(result);return result
