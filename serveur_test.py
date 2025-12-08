#inspiré du code trouvé ici : https://github.com/joeVenner/Python-Chat-Gui-App.git

import socket
import threading

HOST = '127.0.0.1'
PORT = 55555

clients = []
nicknames = []

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

def broadcast(message):  #comme un print mais apparait sur les clients
    for client in clients:
        client.send(message)

def handle(client):
    while True:
        try:
            message = client.recv(1024)
            broadcast(message)
        except:
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                broadcast(f'{nickname} a quitté le chat !'.encode('utf-8'))
                nicknames.remove(nickname)
                break

def receive():
    print(f"serveur {HOST}:{PORT} ")
    while True:
        client, address = server.accept()
        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients.append(client)
        print(f"{nickname} est connecte avec {str(address)}")
        broadcast(f"{nickname} est connecte avec {str(address)}".encode('utf-8'))
        client.send('connecte au serveur'.encode('utf-8'))
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

if __name__ == "__main__":
    receive()