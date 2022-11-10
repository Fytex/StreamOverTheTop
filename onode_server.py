import json
import socket

from threading import Thread
from datetime import datetime

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65000  # Port to listen on (non-privileged ports are > 1023)
JSON_FILE = ""

DATETIME_FMT = '%m/%d/%y %H:%M:%S.%f'

class BootStrap:
    def __init__(self, ips_adjacents):
        self.ips_adjacents = ips_adjacents

    def run(self):
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))

            while True:
                conn, addr = s.accept()

                Thread(target=self.talk_to_conn, args=(conn, addr)).start()

                

    def talk_to_conn(self, conn, addr):
        with conn:
            data = json.dumps(self.ips_adjacents[addr])
            conn.sendall(data)



class ONode_Server:
    def __init__(self, adjacents):
        self.adjacents = adjacents
        self.server = Server(HOST, PORT)

    def run(self):
        pass

    def flood(self):
        for adj_addr in self.adjacents:
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((adj_addr, PORT))

                data = json.dumps((HOST, 0, datetime.utcnow().strftime(DATETIME_FMT)))
                s.sendall(data)

    

def main():
    with open(JSON_FILE) as f:
        ips_adjacents = json.load(f)
        
    server_adjacents = ips_adjacents[HOST]
    
    Thread(target=BootStrap(ips_adjacents).run).start()
    Thread(target=ONode_Server(ips_adjacents).flood).start()


if __name__ == '__main__':
    main()

