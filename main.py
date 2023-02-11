import json
import time
from threading import Thread
import socket

from sqli_connector.sqli_connector import Db as db
import net_utils.net_utils as nu

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 12345
POLL_INTERVAL = 60  # polling interval in seconds

deviceID = "virt_node_1"
# status = {'A1': 'on', 'A2': 'off', 'B1': 'off', 'B2': 'on'}
top_status = {}

host_db = db('hosts.db')

top_hosts = host_db.get_hosts()


class Monitor(Thread):
    __status = {}
    __hosts = []
    __active = 1

    def __init__(self, status, hosts):
        super().__init__()
        self.__status = status
        self.__hosts = hosts

    def stop(self):
        self.__active = 0

    def run(self):
        while self.__active:
            self.check_nodes()
            # print(self.__status)
            time.sleep(60)

    def check_nodes(self):
        activity = nu.check_alive([i[2] for i in self.__hosts])

        for i in range(len(self.__hosts)):
            if activity[i]:
                self.__status[self.__hosts[i][0]] = 'on'
            else:
                self.__status[self.__hosts[i][0]] = 'off'


def do_conn(conn, addr):
    print('connection from: ' + str(addr))
    m = conn.recv(1024).decode()
    ret = {'device_id': deviceID}
    try:
        jdata = json.loads(m)
        if jtype := jdata.get('action_type'):
            ret.update(functable[jtype](jdata))
        else:
            ret['status'] = '789: function type not found'

    except json.decoder.JSONDecodeError:
        ret = {'device_id': deviceID, 'status': '789 : invalid json'}

    ret = json.dumps(ret) + "\n"
    conn.sendall(ret.encode())


def get_nodes(jdata):
    if nodes := jdata.get('nodes'):
        if nodes == '*':
            return top_status
        else:
            ret = {}
            for i in nodes:
                try:
                    ret[i] = top_status[i]
                except KeyError:
                    ret[i] = 'not_found'
        return {'nodes': ret}
    else:
        return {'status' : '789 : node list not found'}


def set_nodes(jdata):
    ret = {}
    nodes = jdata.get('nodes')
    if nodes:
        for i in top_hosts:
            if i[0] in list(nodes.keys()):
                if nodes[i[0]] == 'on' and top_status[i[0]] != 'on':
                    nu.wakeup(i[1])
                elif nodes[i[0]] == 'off' and top_status[i[0]] != 'off':
                    nu.shutdown(i[2])
        m.check_nodes()
        return get_nodes({'nodes': list(nodes.keys())})
    else:
        return {'status': '789: node dict not found'}


def add_node(jdata):
    try:
        return {'status': host_db.add_host(jdata['node_id'], jdata['hostname'], jdata['mac_address'])}
    except json.decoder.JSONDecodeError:
        return {'status': '789: required fields not found'}


def update_node(jdata):
    try:
        return {'status': host_db.update_host(jdata['node_id'], jdata.get('hostname'), jdata.get('mac_address'))}
    except json.decoder.JSONDecodeError:
        return {'status': '789: required fields not found'}


def remove_node(jdata):
    try:
        return {'status': host_db.remove_host(jdata['node_id'])}
    except json.decoder.JSONDecodeError:
        return {'status': '789: required fields not found'}


functable = {'get': get_nodes, 'set': set_nodes, 'add_node': add_node, 'update_node': update_node,
             'remove_node': remove_node}

print('started')
m = Monitor(top_status, top_hosts)
m.start()
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((SERVER_ADDRESS, SERVER_PORT))
    s.listen()
    while True:
        conn, addr = s.accept()
        do_conn(conn, addr)
m.stop()
