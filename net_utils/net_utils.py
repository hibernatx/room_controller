import icmplib
import wakeonlan
import socket


def wakeup(mac):
    wakeonlan.send_magic_packet(mac)
    print('waking up: '+mac)


def check_alive(hostnames):
    return [
        host.is_alive for host in icmplib.multiping(
            [socket.gethostbyname(i) for i in hostnames],
            count=1,
            privileged=False,
            timeout=0.5)
    ]


# stub

def shutdown(host):
    print('shutting down: ' + host)
    pass
