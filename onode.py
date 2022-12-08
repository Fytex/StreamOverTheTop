import sys
import json
import socket

from os import _exit
from copy import deepcopy
from time import perf_counter
from datetime import datetime
from threading import Thread, Lock
from socket import error as SocketError
from routingtable import RoutingTable, UpdateStatus

BOOTSTRAP_PORT = 65000
BOOTSTRAP_IP = sys.argv[1]
FLOOD_PORT = 65521
TRAFFIC_PORT = 65522

TIMEOUT = 5

DATETIME_FMT = '%m/%d/%y %H:%M:%S.%f'

class Adjacents:
    def __init__(self, adjacents=None):
        if adjacents is None:
            adjacents = set()

        self.adjacents = adjacents
        self.active_adjacents = set()
        self.lock = Lock()

    def active(self, addr):
        with self.lock:
            self.active_adjacents.add(addr)

    def inactive(self, addr):
        with self.lock:
            self.active_adjacents.discard(addr)

    def is_active(self, addr):
        with self.lock:
            return addr in self.active_adjacents

    def get_actives(self):
        with self.lock:
            return list(self.active_adjacents)


    def get_all(self):
        return self.adjacents

    def __repr__(self):
        return f"Adjacents({self.adjacents})"


class ONode:
    def __init__(self):
        self.addr = None
        self.adjacents = Adjacents()
        self.routing_tables = {}
        self.stream_ports = {}

    def start(self):
        self.load()
        self.run()

    def load(self):
        self.connect_bootstrap()
        print("Got adjacents  -> " + str(self.adjacents))
        self.flood()


    '''

    Bootstrap

    '''

        
    def connect_bootstrap(self, server_stream=None):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((BOOTSTRAP_IP, BOOTSTRAP_PORT))
        
            data = pkg = s.recv(1024)
            while pkg:
                pkg = s.recv(1024)
                data += pkg

        info = json.loads(data.decode())
        self.load_info(info, server_stream)


    def load_info(self, info, server_stream=None):
        self.addr = info['addr']
        self.adjacents = Adjacents(info['adjacents'])
        self.stream_ports = info['stream_ports']

        for stream, port in self.stream_ports.items():
            self.routing_tables[stream] = RoutingTable(stream, port)
        
        if server_stream: # Server only
            self.routing_tables[server_stream].update({
                'path': [self.addr],
                'stream': server_stream,
                'delta_server': 0,
                'version': 0
            })


    '''

    Flood

    '''



    def flood(self):
        self.pre_flood_all()
        
        Thread(target=self.receive_flood).start()
        


    def receive_flood(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.addr, FLOOD_PORT))
            s.listen()
            
            while True:
                print("Listening " + self.addr + ":" + str(FLOOD_PORT))
                conn, addr_port = s.accept()
                Thread(target=self.process_flood_info, args=(conn, addr_port[0])).start()


    def process_flood_info(self, conn, addr):
        data = pkg = conn.recv(4096).decode()
        
        while pkg:
            pkg = conn.recv(4096).decode()
            data += pkg
            
        info = json.loads(data)
        node_type = info['type']
        value = info['value']

        print(f"Received Info from {addr}: {info}")

        if node_type == 'Node':
            self.process_flood_info_node(addr)
        else:
        
            stream = value['stream']
            routing_table = self.routing_tables[stream]

            if node_type == 'Client':
                self.process_flood_info_client(routing_table, info, addr)
            elif node_type == 'Server':
                self.process_flood_info_server(routing_table, info, addr)
            else:
                raise Exception(f"{node_type} not exepcted")

            print(routing_table)


    def process_flood_info_client(self, routing_table, info, addr):
        status = info['value']['status']

        # Client requesting Info about stream
        if status is None:
            value = routing_table.get_metrics()

            if value:
                info = {
                    'type': 'Server',
                    'value': value
                }
                self.flood_info_adj(addr, info)
            return



        print(f"Status {info['value']['status']} - {id(routing_table)}")
        has_updated = False
            
        if status:
            if routing_table.is_available():
                has_updated = routing_table.add(addr)
        else:
            has_updated = routing_table.remove(addr)
            

        if has_updated:
            prev_node = routing_table.get_prev_node()
            if prev_node:
                self.flood_info_adj(prev_node, info)


    def process_flood_info_node(self, addr):
        for routing_table in self.routing_tables.values():
            value = routing_table.get_metrics()

            if value:
                info = {
                    'type': 'Server',
                    'value': value
                }
                self.flood_info_adj(addr, info)
        

    def process_flood_info_server(self, routing_table, info, addr):
        value = info['value']
        value['path'].append(self.addr)

        update_status, old_prev_node = routing_table.update(value)

        
            

        if update_status:
            if ((update_status == UpdateStatus.UPDATED and old_prev_node != addr) or        \
                (update_status == UpdateStatus.RESTARTED and old_prev_node == addr)         \
            ) and routing_table.get_next_nodes():
                self.update_stream_from_node(routing_table.stream, addr, 1)

                
            if update_status == UpdateStatus.UPDATED and old_prev_node:
                self.update_stream_from_node(routing_table.stream, old_prev_node, 0)

            self.flood_info(info, update_status)
        

    def flood_info(self, info, update_status):
        
        for adj_addr in self.adjacents.get_actives():
            if adj_addr not in info['value']['path']:
                Thread(target=self.flood_info_adj, args=(adj_addr, deepcopy(info))).start()
    
    def flood_info_adj(self, adj_addr, info):
            
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.addr, 0))
            print(f"Connecting to {adj_addr} from {self.addr}")
            connected = False
            start_time = perf_counter()

            while not connected:
                try:
                    s.connect((adj_addr, FLOOD_PORT))
                except SocketError:
                    current_time = perf_counter()

                    if current_time - start_time > TIMEOUT:
                        self.adjacents.inactive(adj_addr)

                        incoming_nodes = []
                        
                        for routing_table in self.routing_tables.values():
                            incoming_nodes.append(routing_table.get_prev_node())
                            routing_table.disabled_node(adj_addr)

                        # Just ask for info if we need to update our incomes for one routing_table
                        if any(adj_addr == node for node in incoming_nodes):
                            self.pre_flood_all()

                        return
                else:
                    connected = True
                    self.adjacents.active(adj_addr)


            if info['type'] == 'Server':
                info['value']['datetime_origin'] = datetime.utcnow().strftime(DATETIME_FMT)
            
            data = json.dumps(info)
            s.sendall(data.encode())


    def update_stream_from_node(self, stream, addr, status):

        info = {
            'type': 'Client',
            'value': {
                'stream': stream,
                'status': status
            }
        }

        self.flood_info_adj(addr, info)


    def pre_flood_all(self):
        for adj_addr in self.adjacents.get_all():
            Thread(target=self.pre_flood, args=(adj_addr,)).start()


    def pre_flood(self, addr):
        info = {
            'type': 'Node',
            'value': None
        }

        self.flood_info_adj(addr, info)

    '''

    Run

    '''

    def run(self):
        for routing_table in self.routing_tables.values():
            Thread(target=self.run_stream, args=(routing_table, )).start()

    def run_stream(self, routing_table):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.addr, routing_table.port))

        s.settimeout(TIMEOUT)

        while True:
            
            try:
                pkg, addr_port = s.recvfrom(20480)
            except socket.timeout:
                prev_node = routing_table.get_prev_node()
                if prev_node and routing_table.get_next_nodes():
                    routing_table.disabled_node(prev_node)
                    Thread(target=self.update_stream_from_node, args=(routing_table.stream, prev_node, 0)).start()
                    self.pre_flood_all()
                continue
                    
            addr, _ = addr_port
            #print(f"Traffic: {addr}: {pkg}")

            print(routing_table.get_next_nodes())
            nodes = routing_table.get_next_nodes()
            
            if not nodes and addr != self.addr: # addr != self.addr is for server loopback
                Thread(target=self.update_stream_from_node, args=(routing_table.stream, addr, 0)).start()
            for next_addr in nodes:
                s.sendto(pkg, (next_addr, routing_table.port))

    def stop(self):
        threads = []
        for stream, routing_table in self.routing_tables.items():
            prev_node = routing_table.prev_node # Force access
            next_nodes = routing_table.next_nodes # Force access
            print(f"Closing {stream} - {prev_node}")
            if prev_node and next_nodes:
                t = Thread(target=self.update_stream_from_node, args=(stream, prev_node, 0))
                t.start()
                threads.append(t)

        print("Joining")
        for t in threads:
            t.join()
        print("Joined")
        _exit(0)
        

def main():
    node = ONode()
    
    try:
        node.start()
    except:
        node.stop()
        
        


if __name__ == '__main__':
    main()
