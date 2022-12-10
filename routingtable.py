from read_write_lock import get_RWLocks, read_lock, write_lock

class UpdateStatus:
    NOTHING = 0
    UPDATED = 1
    MONITOR = 2
    RESTARTED = 3

class RoutingTable:
    def __init__(self, stream, port):
        self.stream = stream
        self.port = port
        self.path = []
        self.versions = {} # Dictionary to allow multiple servers streaming same content
        self.delta_server = None
        self.next_nodes = set()

        self.read_lock, self.write_lock = get_RWLocks()

    @property
    def prev_node(self):
        try:
            return self.path[-2]
        except IndexError:
            return None

    @property
    def available(self):
        return len(self.path) > 0
    

    @read_lock
    def get_metrics(self): # ReadLock
        if not self.available:
            return None
        
        server = self.path[0]
        
        return {
            'path': self.path.copy(),
            'stream': self.stream,
            'delta_server': self.delta_server,
            'version': self.versions[server]
        }


    @read_lock
    def get_current_version(self): # ReadLock
        server = self.path[0]
        version = self.versions[server]
        return version
    

    @write_lock
    def update(self, value): # WriteLock
        '''
        Either updated RoutingTable or new version update
        New version update returns None as old_prev_node
        just to force flood (monitor) without closing connection
        '''
        
        new_path = value['path']
        new_version = value['version']
        new_server = new_path[0]

        old_prev_node = self.prev_node
        
        
        if self.path:
            new_prev_node = new_path[-2]
            current_version = self.versions.get(new_server)

            if old_prev_node == new_prev_node:
                self.path = new_path

            def check():
                return old_prev_node != new_prev_node and \
                       (len(self.path) > len(new_path))
            print(self.path)
            print(new_path)
            if not check():
                
                # Propagate if restarted or monitorization
                if new_version == 0:
                    self.versions[new_server] = new_version
                    return (UpdateStatus.RESTARTED, old_prev_node)
                
                elif not current_version or new_version > current_version:
                    self.versions[new_server] = new_version
                    return (UpdateStatus.MONITOR, None)

                else:
                    return (UpdateStatus.NOTHING, None)


        print(f"\n\n\n\nUPDATED\n\n\n\n{new_path}\n\n\n\n\n")
        
        self.path = new_path.copy()
        self.versions[new_server] = new_version
        
        return (UpdateStatus.UPDATED, old_prev_node)

    
    @read_lock
    def get_prev_node(self): # ReadLock
        return self.prev_node

    @read_lock
    def get_next_nodes(self): # ReadLock
        return list(self.next_nodes)

    @read_lock
    def add(self, addr): # WriteLock
        self.next_nodes.add(addr)

        return len(self.next_nodes) == 1

    @write_lock
    def remove(self, addr): # WriteLock
        self.next_nodes.discard(addr)

        return len(self.next_nodes) == 0

    @read_lock
    def is_available(self): # ReadLock
        return self.available

    def disabled_node(self, addr):
        
        with self.read_lock:
            if addr != self.prev_node and addr not in self.next_nodes:
                return

        with self.write_lock:
            if addr == self.prev_node:
                self.path = []
            else:
                self.next_nodes.discard(addr)
                

    def __repr__(self):
        return f'RoutingTable({self.stream}, {self.prev_node}, {self.next_nodes})'
