import json
import time
from threading import Thread
import socket

from sqli_connector.sqli_connector import Db as db
import net_utils.net_utils as nu

SERVER_ADDRESS = "0.0.0.0"
SERVER_PORT = 1234
POLL_INTERVAL = 60  # polling interval in seconds
print('listening on: ', SERVER_ADDRESS, " Port: ", SERVER_PORT)
deviceID = "59-3229"
#status = {'A1': 'on', 'A2': 'off', 'B1': 'off', 'B2': 'on'}
top_status = {}
fake_status = {'59-3229-2' : 'off'}
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
        if nodes == 'fake':
            return {'nodes' : fake_status }
        
        elif nodes == '*':
            r = {}
            r.update(fake_status)
            r.update(top_status)
            return { 'nodes' : r }
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
    global top_hosts
    ret = {}
    nodes = jdata.get('nodes')
    if nodes:
        for i in nodes.keys():
            if i in list(fake_status.keys()):
                if fake_status[i] == 'off':
                    if nodes[i] == 'on':
                        ret[i] = 'on'
                        fake_status[i] == 'on'
                    else:
                        ret[i] = 'already_on'
                elif fake_status['A0'] == 'on':
                    if nodes[i] == 'off':
                        ret[i] = 'off'
                        fake_status[i] = 'off'
                    else:
                        ret[i] = 'already_off'
                        
        
        for i in top_hosts:
            if i[0] in nodes.keys():
                if nodes[i[0]] == 'on':
                    if top_status[i[0]] != 'on':
                        nu.wakeup(i[1])
                    else:
                        ret[i[0]] = 'already_on'
                elif nodes[i[0]] == 'off':
                    if top_status[i[0]] != 'off':
                        nu.shutdown(i[2])
                    else:
                        ret[i[0]] = 'already_off'
        m.check_nodes()
        data = get_nodes({'nodes': list(nodes.keys())})
        data['nodes'].update(ret)
        return data
    else:
        return {'status': '789: node dict not found'}


def add_node(jdata):
    global top_hosts
    try:
        x =  {'status': host_db.add_host(jdata['node_id'], jdata['hostname'], jdata['mac_address'])}
        top_hosts = host_db.get_hosts()
        return x
    except json.decoder.JSONDecodeError:
        return {'status': '789: required fields not found'}


def update_node(jdata):
    global top_hosts
    try:
        print(str(jdata.get("hostname")))
        print(str(jdata.get("mac_address")))
        x =  {'status': host_db.update_host(jdata['node_id'], jdata.get("hostname"), jdata.get("mac_address"))}
        top_hosts = host_db.get_hosts()
        return x
    except json.decoder.JSONDecodeError:
        return {'status': '789: required fields not found'}


def remove_node(jdata):
    global top_hosts
    try:
        x = {'status': host_db.remove_host(jdata['node_id'])}
        top_hosts = host_db.get_hosts()
        return x
    except json.decoder.JSONDecodeError:
        return {'status': '789: required fields not found'}


functable = {'Get': get_nodes, 'Set': set_nodes, 'AddNode': add_node, 'UpdateNode': update_node,
             'RemoveNode': remove_node}

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
