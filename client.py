#inspiré du code trouvé ici : https://github.com/joeVenner/Python-Chat-Gui-App.git

import socket
import threading
import sys
import random
import cryptage
import time

if len(sys.argv) < 3:
    print(f"Usage : python {sys.argv[0]} <IP_MASTER> <PORT_MASTER>")
    sys.exit(1)

master_ip = sys.argv[1]
master_port = int(sys.argv[2])
BLOC_TAILLE = 3


def adresse_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


class Client:
    def __init__(self):
        self.ip = adresse_ip()
        self.pseudo = input("Entrez votre pseudo : ")
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind(('0.0.0.0', 0))
        self.port = self.server_sock.getsockname()[1]
        print(f"\nCLIENT : {self.pseudo} | IP: {self.ip} | PORT: {self.port}\n")
        self.enregistrement_db()

        # Lancement des threads
        threading.Thread(target=self.reception_message, daemon=True).start()
        threading.Thread(target=self.ping, daemon=True).start()

    def enregistrement_db(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((master_ip, master_port))
            msg = f"REG|CLIENT|{self.pseudo}|{self.port}|0|0"
            s.send(bytes(msg, 'utf-8'))
            resp = s.recv(1024).decode('utf-8')
            s.close()
            if resp != "OK": sys.exit(1)
            print("[SUCCES] Connecte au Master.")
        except:
            sys.exit(1)

    def ping(self):
        """Envoie un PING au master toutes les 10 secondes"""
        while True:
            time.sleep(10)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((master_ip, master_port))
                s.send(bytes(f"PING|{self.port}", 'utf-8'))
                s.close()
            except:
                pass  # Si le master est eteint, on ne plante pas, on reessaie plus tard

    def reception_message(self):
        self.server_sock.listen()
        while True:
            try:
                conn, _ = self.server_sock.accept()
                msg = conn.recv(4096).decode('utf-8')
                if msg:
                    print(f"\n\nMESSAGE RECU : {msg.replace('FINAL:', '')}")
                    print("Appuyez sur Entree...", end="", flush=True)
                conn.close()
            except:
                break

    def liste_client_routeur(self, cmd):
        """recois la liste des clients et des routeurs et la transforme en dictionnaire"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((master_ip, master_port))
            s.send(bytes(cmd, 'utf-8'))
            data = s.recv(16384).decode('utf-8')
            s.close()
            nodes = []
            for item in data.split(';'):
                if item:
                    p = item.split(',')
                    nodes.append({"nom": p[0], "ip": p[1], "port": int(p[2]), "n": int(p[3]), "e": int(p[4])})
            return nodes
        except:
            return []

    def couche_onion(self, message, path, dest_ip, dest_port):
        message_final = f"{dest_ip}:{dest_port}:{message}"
        for i in range(len(path) - 1, -1, -1):
            node = path[i]
            pub = (node['n'], node['e'])
            if i == len(path) - 1:
                next_hop = "FINAL"
            else:
                next_hop = f"{path[i + 1]['ip']}:{path[i + 1]['port']}"
            data = f"{next_hop}|{message_final}"
            liste = cryptage.chiffrer(data, pub, BLOC_TAILLE)
            message_final = "_".join(str(x) for x in liste)
        return message_final

    def interface_client(self):
        while True:
            print("\n1. Envoyer | 2. Quitter")
            if input("Choix: ") == "2": break

            clients = self.liste_client_routeur("GET_CLIENTS")
            cibles = [c for c in clients if c['nom'] != f"CLIENT_{self.pseudo}"]
            if not cibles:
                print("Pas de destinataire.")
                continue

            for i, c in enumerate(cibles):
                print(f"{i + 1}. {c['nom'].replace('CLIENT_', '')}")

            try:
                dest = cibles[int(input("Numero: ")) - 1]
            except:
                continue

            msg = input("Message: ")

            routers = self.liste_client_routeur("GET_ROUTERS")
            if not routers:
                print("Pas de routeurs !")
                continue

            nb_sauts = random.randint(1, min(len(routers), 5))
            path = random.sample(routers, nb_sauts)
            print(f"[*] Route : {[r['nom'] for r in path]}")

            try:
                onion = self.couche_onion(msg, path, dest['ip'], dest['port'])
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((path[0]['ip'], path[0]['port']))
                s.send(bytes(onion, 'utf-8'))
                s.close()
                print("[SUCCES] Envoye !")
            except Exception as e:
                print(f"[ERREUR] {e}")


if __name__ == "__main__":
    Client().interface_client()
