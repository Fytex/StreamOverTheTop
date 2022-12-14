import json
import socket

from threading import Thread

JSON_FILE = "ips_adj.json"

BOOTSTRAP_PORT = 65000

STREAM_PORTS = {
    'movie.Mjpeg': 65522
}

class BootStrap:
    def __init__(self, bootstrap_addr):

        with open(JSON_FILE) as f:
            info = json.load(f)
        
        self.nodes = info.get('Nodes')
        self.adjacents = info.get('Adjacents')
        self.bootstrap_addr = bootstrap_addr
        

    def get_addr_adjacents(self, addr):
        node = next(node for node, addrs in self.nodes.items() if addr in addrs)
         
        return (self.nodes[node][0], [self.nodes[adj_node][0] for adj_node in self.adjacents[node]])


    def get_node_info(self, addr):
        static_addr, adjs = self.get_addr_adjacents(addr)
        
        return {
            'addr': static_addr,
            'adjacents': adjs ,
            'stream_ports': STREAM_PORTS
        }

    def run(self):
        print("Bootstrapper: Listening...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.bootstrap_addr, BOOTSTRAP_PORT))
            s.listen()

            while True:
                conn, addr_port = s.accept()
                print('Bootstrapper: IP Connection - '+ str(addr_port[0]))
                Thread(target=self.talk_to_conn, args=(conn, addr_port[0])).start()
                

    def talk_to_conn(self, conn, addr):
        with conn:
            
            info = self.get_node_info(addr)
            
            data = json.dumps(info)
            conn.sendall(data.encode())


    



if __name__ == '__main__':
    BootStrap().run()
