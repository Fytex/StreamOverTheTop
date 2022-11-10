import socket

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65521  # Port to listen on (non-privileged ports are > 1023)
BOOTSTRAP_IP = "127.0.0.1"
BOOTSRAP_PORT = 65000

class Node:
    def __init__(self):
        self.adjacents = []
        self.connections = {}
    
    def connect_bootstrap():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((BOOTSTRAP_IP, BOOTSTRAP_PORT))
        
            tup_defs = s.recv(1024)
            self.adjacents  = tup_defs.json.loads(tup_defs)
    
    def flood(self): #Needs to maintain connections open with adjacents
        
        
        


def main():


if __name__ == '__main__':
    main()
