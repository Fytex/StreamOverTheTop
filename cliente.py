import socket
import sys

def main():
    s : socket.socket
    msg : str

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    msg = "Adoro Redes :)"

    s.sendto(msg.encode('utf-8'), ('127.0.0.1', int(sys.argv[1])))
    resposta, server_add = s.recvfrom(1024)

    print(f"Recebi {resposta.decode('utf-8')} do servidor {server_add}")

    s.close()

if __name__ == "__main__":
    main()
