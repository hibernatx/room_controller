import icmplib
import wakeonlan
import socket


def wakeup(mac):
    try:
        wakeonlan.send_magic_packet(mac)
    except:
        pass
    print('waking up: '+mac)


def check_alive(hostnames):
    return [
        host.is_alive for host in icmplib.multiping(
            [socket.gethostbyname(i) for i in hostnames],
            count=1,
            timeout=0.5,
            privileged=False)
    ]


# stub

def shutdown(host):
    print('shutting down: ' + host)
    pass
