import socket
import threading
import time

def processamento(s : socket, msg : bytes, address : tuple):
    for x in range(9):
        print(f"Recebi {msg.decode('utf-8')} do cliente {address}")
        time.sleep(1)

    s.sendto("Correu bem".encode('utf-8'), address)

def processamento2(s : socket, msg : bytes, address : tuple):
    for x in range(9):
        print(f"SUCESIUM")
        time.sleep(1)

    s.sendto("SUCESIUM".encode('utf-8'), address)

def servico():
    s : socket.socket
    endereco : str
    port : int
    msg : bytes
    add : tuple

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    endereco = '127.0.0.1'
    port = 3000

    s.bind((endereco, port))

    print(f"Estou à escuta no {endereco}:{port}")

    while True:
        msg, add = s.recvfrom(1024)
        threading.Thread(target=processamento, args=(s, msg, add)).start()

    s.close()

def servico2():
    s : socket.socket
    endereco : str
    port : int
    msg : bytes
    add : tuple

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    endereco = '10.0.0.10'
    port = 4000

    s.bind((endereco, port))

    print(f"Estou à escuta no {endereco}:{port}")

    while True:
        msg, add = s.recvfrom(1024)
        threading.Thread(target=processamento2, args=(s, msg, add)).start()

    s.close()
       
def main():
    threading.Thread(target=servico, args=()).start()
    #threading.Thread(target=servico2, args=()).start()

if __name__ == '__main__':
    main()
