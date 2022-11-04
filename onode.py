import socket

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65521  # Port to listen on (non-privileged ports are > 1023)
BOOTSTRAP_IP = "127.0.0.1"
BOOTSRAP_PORT = 65000

class Node:
    def __init__(self):
        self.neighbours = []
        self.connections = {}
    
    def connect_bootstrap():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((BOOTSTRAP_IP, BOOTSTRAP_PORT))
        
        tup_defs = s.recv(1024)
        self.neighbours = tup_defs.json.loads(tup_defs)
        
        s.close()
    
    def connect_with_neighbours(self): #Needs to maintain connections open with neighbours
        pass
            
        

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Hello, world")
    data = s.recv(1024)

    print(f"Received {data!r}")
'''
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)
'''
