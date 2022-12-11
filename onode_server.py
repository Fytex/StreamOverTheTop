import sys
import json
import socket



from time import sleep
from datetime import datetime
from socket import error as SocketError
from threading import Thread, Lock, Event

from onode import ONode, FLOOD_PORT, BOOTSTRAP_IP, DATETIME_FMT

from stream_service.Servidor import Servidor



IS_MAIN_NODE = False

STREAM = sys.argv[2]




class ONode_Server(ONode):

    #Overwrite
    def __init__(self, info):
        super().__init__()

        self.info = info

    
    #Overwrite
    def connect_bootstrap(self):
        if IS_MAIN_NODE:
            self.load_info(self.info, STREAM)
        else:
            super().connect_bootstrap(STREAM)

    #Overwrite
    def process_flood_info_node(self, addr):
        
        # 'datetime_origin' will be added before sent
        info = {
            'type': 'Server',
            'value': {
                'path': [self.addr],
                'stream': STREAM,
                'delta_server': 0
            }
        }

        
        self.flood_info_adj(addr, info)

    #Overwrite
    def process_flood_info_server(self, *args, **kwargs):
        pass



    def _pre_flood_and_monitor(self):
        threads = []
        all_adjacents = self.adjacents.get_all()
        
        for adj_addr in all_adjacents:
                t = Thread(target=self.process_flood_info_node, args=(adj_addr,))
                threads.append(t)
                t.start()


        
        while True:
            sleep(10)
            
            for adj_addr in self.adjacents.get_actives():
                idx = all_adjacents.index(adj_addr)
                
                if not threads[idx].is_alive():
                    t = Thread(target=self.process_flood_info_node, args=(adj_addr,))
                    threads[idx] = t
                    t.start()
            


    #Overwrite
    def pre_flood_all(self):
        Thread(target=self._pre_flood_and_monitor).start()
    
    

        
    '''

    Run

    '''

    #Overwrite
    def run(self):
        
        routing_table = self.routing_tables[STREAM]

        stream_service = Servidor().main(STREAM, self.addr, routing_table.port)
        self.run_stream(routing_table)
        
        #s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #s.bind((self.addr, routing_table.port))
        print(f"Enviando... {id(routing_table)} - {routing_table}")
        '''
        while True:
            for next_addr in routing_table.get_next_nodes():
                s.sendto(f"{STREAM}: Sent...".encode(), (next_addr, routing_table.port))
                sleep(1)
        '''
        '''
        for next_addr in self.adjacents.get_all():
            stream_service = Servidor().main(STREAM, next_addr, routing_table.port)
        '''

                

    

def main():
    info = {}

    try:
        arg = sys.argv[3]
    except IndexError:
        pass
    else:
        assert(arg == 'bootstrap')

        global IS_MAIN_NODE
        IS_MAIN_NODE = True

        bootstrap = __import__('bootstrap').BootStrap(BOOTSTRAP_IP)
        Thread(target=bootstrap.run).start()
        
        info = bootstrap.get_node_info(BOOTSTRAP_IP)


    print("Run Server")
    
    ONode_Server(info).start()


if __name__ == '__main__':
    main()

