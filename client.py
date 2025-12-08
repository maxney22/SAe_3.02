#inspiré du code trouvé ici : https://github.com/joeVenner/Python-Chat-Gui-App.git

import socket
import threading

nickname = input("Choisis ton pseudo : ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55555))

def receive():
    while True:
            message = client.recv(1024).decode('utf-8')
            if message == 'NICK':
                client.send(nickname.encode('utf-8'))
            else:
                print(message)


def write():
    while True:
            text = input("")
            message = f'{nickname}: {text}'
            client.send(message.encode('utf-8'))


receive_thread = threading.Thread(target=receive)
receive_thread.start()
write_thread = threading.Thread(target=write)
write_thread.start()