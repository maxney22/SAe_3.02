import socket
import threading
from importlib.resources import contents

id = input("Nom du routeur : ")
listen_port = int(input("Port du routeur : "))

def handle_client(conn):
    message = conn.recv(1024).decode("utf-8")
    part = message.split(":",3)

    next_hop = part[0]
    next_port = part[1]
    content = part [2]
    print(f"[{id}] reçu : {content} destination {next_hop}:{next_port}")
    print(f"[{id}] → Relayage vers {next_hop}:{next_port}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((next_hop, next_port))
    s.send(content.encode("utf-8"))
    s.close()


def listen():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", listen_port))
    server.listen()
    print(f"[{id}] En écoute sur le port {listen_port}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn,)).start()


listen()
