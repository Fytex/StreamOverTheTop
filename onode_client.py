import sys
import json
import socket

from threading import Thread
from onode import ONode, FLOOD_PORT
from socket import error as SocketError

from routingtable import UpdateStatus
from stream_service.Cliente import Cliente

STREAM = sys.argv[2]

class ONodeClient(ONode):

    '''

    Flood

    '''

    # Overwrite
    def flood_info(self, info, update_status):
        if update_status != UpdateStatus.UPDATED:
            return

        prev_addr = info['value']['path'][-2] # -1 is this node

        self.update_stream_from_node(STREAM, prev_addr, 1)

    #Overwrite
    def process_flood_info_client(self, *args, **kwargs):
        pass

    #Overwrite
    def process_flood_info_node(self, *args, **kwargs):
        pass

    #Overwrite
    def process_flood_info_server(self, routing_table, info, addr):
        if routing_table.stream == STREAM:
            super().process_flood_info_server(routing_table, info, addr)

    #Overwrite
    def pre_flood(self, addr):
        self.update_stream_from_node(STREAM, addr, None)
        
    '''

    RUN
    
    '''

    # Overwrite
    def run(self):
        '''
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.addr, self.stream_ports[STREAM]))

        while True:
            pkg, addr_port = s.recvfrom(4096)
            print(f"Traffic: {addr_port[0]}: {pkg}")
        '''
        print(f"---------------\n\n\n{self.addr} - {self.stream_ports[STREAM]}\n\n\n")
        routing_table = self.routing_tables[STREAM]

        routing_table.add('127.0.0.1')
        Thread(target=self.run_stream, args=(routing_table, )).start()
        Cliente().main('127.0.0.1', self.stream_ports[STREAM])

        

def main():
    client = ONodeClient()
    
    try:
        client.start()
    except:
        client.stop()


if __name__ == '__main__':
    main()
