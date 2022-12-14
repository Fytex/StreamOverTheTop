from read_write_lock import get_RWLocks, read_lock, write_lock

BOOST_STD_DEV = 0.1 # 10%
TIME_MIN_MARGIN = 50 * (10**3) # 50ms

class UpdateStatus:
    NOTHING = 0
    UPDATED = 1
    MONITOR = 2

class RoutingTable:
    def __init__(self, stream, port):
        self.stream = stream
        self.port = port
        self.path = []
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
            'delta_server': self.delta_server
        }
    

    @write_lock
    def update(self, value): # WriteLock

        new_path = value['path']
        new_server = new_path[0]

        new_delta_server = value['delta_server']

        old_prev_node = self.prev_node
        
        
        if self.path:
            new_prev_node = new_path[-2]

            if old_prev_node == new_prev_node:
                self.path = new_path
                self.delta_server = new_delta_server
                return (UpdateStatus.MONITOR, None)

            def check():
                if self.delta_server < TIME_MIN_MARGIN and new_delta_server < TIME_MIN_MARGIN:
                    return len(self.path) > len(new_path)

                
                boost = (self.delta_server - new_delta_server) / self.delta_server

                if boost > BOOST_STD_DEV:
                    return True
                elif boost > -BOOST_STD_DEV:
                    return len(self.path) > len(new_path)
                else:
                    return False

            
            if not check():
                    return (UpdateStatus.NOTHING, None)

        
        self.path = new_path.copy()
        self.delta_server = new_delta_server
        
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
