import socket
import threading
import sys
import random
import cryptage #nom de notre fichier de cryptage
import time
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit,
                             QGroupBox, QComboBox, QMessageBox)
from PyQt6.QtCore import pyqtSignal, QObject, QTimer, Qt

BLOC_TAILLE = 3 # variable pour cryptage
master_ip = ""
master_port = 0

def adresse_ip():
    try:
        socket_envoi = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_envoi.connect(("8.8.8.8", 80))
        ip = socket_envoi.getsockname()[0]
        socket_envoi.close()
        return ip
    except:
        return "127.0.0.1"


class Client:
    def __init__(self, pseudo_gui=None, callback_gui=None):
        global master_ip, master_port
        self.ip = adresse_ip()
        self.callback_gui = callback_gui
        if pseudo_gui:
            self.pseudo = pseudo_gui
        else:
            self.pseudo = input("Entrez votre pseudo : ")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', 0))
        self.port = self.server_socket.getsockname()[1]
        self.enregistrement_db()
        print(f"\nClient {self.pseudo} -> IP: {self.ip} Port: {self.port}\n")
        threading.Thread(target=self.reception_message, daemon=True).start()
        threading.Thread(target=self.ping, daemon=True).start()

    def enregistrement_db(self):
        socket_envoi = None
        try:
            socket_envoi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_envoi.settimeout(2.0)
            socket_envoi.connect((master_ip, master_port))
            message_enregistrement = f"ENRE|CLIENT|{self.pseudo}|{self.port}|0|0"
            socket_envoi.send(bytes(message_enregistrement, 'utf-8'))
            reponse_master = socket_envoi.recv(1024).decode('utf-8')
            socket_envoi.close()
            if reponse_master != "OK":
                raise Exception("Erreur d'enregistrement")
            print("Connecte au Master.")

        except socket.timeout:
            if socket_envoi: socket_envoi.close()
            raise Exception("Délai d'attente dépassé verifié l'adresse IP")

    def ping(self):
        while True:
            time.sleep(2)
            try:
                socket_envoi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                socket_envoi.settimeout(1)  # timeout sur la socket sinon elle se ferme avant qu'il puisse envoyer l'info
                socket_envoi.connect((master_ip, master_port))
                socket_envoi.send(bytes(f"PING|{self.port}", 'utf-8'))
                socket_envoi.close()
            except:
                pass

    def reception_message(self):
        self.server_socket.listen()
        while True:
            try:
                conn, _ = self.server_socket.accept()

                gros_paquet = b""
                while True:
                    paquet = conn.recv(4096)
                    if not paquet:
                        break
                    gros_paquet += paquet

                message_FINAL = gros_paquet.decode('utf-8')

                if message_FINAL:
                    message = message_FINAL.replace('FINAL:', '')
                    print(f"\n\nMessage reçu : {message}")
                    if self.callback_gui:
                        self.callback_gui(message)
                conn.close()
            except:
                break

    def liste_client_routeur(self, cmd):
        try:
            socket_envoie = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_envoie.settimeout(2.0)
            socket_envoie.connect((master_ip, master_port))
            socket_envoie.send(bytes(cmd, 'utf-8'))
            data = socket_envoie.recv(16384).decode('utf-8')
            socket_envoie.close()
            nodes = []
            for item in data.split(';'):
                if item:
                    p = item.split(',')
                    nodes.append({"nom": p[0], "ip": p[1], "port": int(p[2]), "n": int(p[3]), "e": int(p[4])})
            return nodes
        except:
            return []

    def couche_onion(self, message, route_routeurs, ip_destination, port_destination):
        message_dernier_routeur = f"{ip_destination}:{port_destination}:{message}"
        prochain_saut = "FINAL"
        for routeur in reversed(route_routeurs):
            cle_publique = (routeur['n'], routeur['e'])
            paquet_chiffrer = f"{prochain_saut}|{message_dernier_routeur}"
            liste_nombres_chiffre = cryptage.chiffrer(paquet_chiffrer, cle_publique, BLOC_TAILLE)

            liste_en_texte = []
            for nombre in liste_nombres_chiffre:
                nombre_en_str = str(nombre)
                liste_en_texte.append(nombre_en_str)

            message_dernier_routeur = "_".join(liste_en_texte)
            prochain_saut = f"{routeur['ip']}:{routeur['port']}"

        return message_dernier_routeur

class FenetreConnexion(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connexion Client")
        self.resize(300, 200)

        layout = QVBoxLayout()
        self.input_ip = QLineEdit("")
        self.input_ip.setPlaceholderText("Ex: 192.168.x.x ou localhost")
        self.input_port = QLineEdit("")
        self.input_port.setPlaceholderText("Ex: 20000")
        self.input_pseudo = QLineEdit("")
        self.input_pseudo.setPlaceholderText("John Doe")
        self.btn_co = QPushButton("Se Connecter")
        self.btn_co.clicked.connect(self.connecter)

        layout.addWidget(QLabel("IP Master:"))
        layout.addWidget(self.input_ip)
        layout.addWidget(QLabel("Port Master:"))
        layout.addWidget(self.input_port)
        layout.addWidget(QLabel("Pseudo :"))
        layout.addWidget(self.input_pseudo)
        layout.addWidget(self.btn_co)

        self.setLayout(layout)

    def connecter(self):
        global master_ip, master_port
        pseudo = self.input_pseudo.text()

        if not pseudo or not self.input_ip.text() or not self.input_port.text():
            QMessageBox.warning(self, "Erreur champs", "Veuillez remplir IP Port et Pseudo")
            return

# erreur si il y a des caractère interdit sinon ça créer des problème avec les vrai séparateur dans le code
        caracteres_interdits = [";", ":", ",", "|"]
        for caractere in caracteres_interdits:
            if caractere in pseudo:
                QMessageBox.warning(self,"Attention",f"les caractères {caracteres_interdits} sont interdits""")
                return

        master_ip = self.input_ip.text()

        try:
            master_port = int(self.input_port.text())
        except ValueError:
            QMessageBox.critical(self, "Erreur", "Le port doit être un nombre")
            return

        try:
            socket_verif = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_verif.settimeout(2.0)
            socket_verif.connect((master_ip, master_port))

            socket_verif.send(bytes("LISTE_CLIENT", 'utf-8'))
            reponse = socket_verif.recv(16384).decode('utf-8')
            socket_verif.close()
            nom_voulu = f"CLIENT_{pseudo}"

            if reponse:
                clients_existants = reponse.split(';')
                for client_str in clients_existants:
                    if client_str:
                        infos = client_str.split(',')
                        nom_existant = infos[0]
                        if nom_existant == nom_voulu:
                            QMessageBox.warning(self, "Attention",f"Le pseudo '{pseudo}' est déjà pris par un client dans le réseau")
                            return

        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de vérifier le pseudo problème de connexion : {e}")
            return

        try:
            client_logique = Client(pseudo_gui=pseudo, callback_gui=None)
            self.fenetre_chat = FenetreMessagerie(client_logique)
            self.fenetre_chat.show()
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Erreur Connexion", f"{e}")


class FenetreMessagerie(QWidget):

    signal_reception = pyqtSignal(str)

    def __init__(self, client_logique):
        super().__init__()
        self.client_logique = client_logique
        self.setWindowTitle(f"Client {self.client_logique.pseudo}")
        self.resize(800, 500)

        self.client_logique.callback_gui = self.signal_reception.emit
        self.signal_reception.connect(self.afficher_message_recu)

        layout = QGridLayout()

        info_utilisateur = f"{self.client_logique.pseudo}  -->  IP {self.client_logique.ip} Port: {self.client_logique.port}"
        zone_info_utilisateur = QLabel(info_utilisateur)
        zone_info_utilisateur.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 5px;")
        zone_info_utilisateur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(zone_info_utilisateur, 0, 0, 1, 2)

        objet_gauche = QVBoxLayout()
        self.zone_boite_lettre = QLabel("Boite au lettre :")
        objet_gauche.addWidget(self.zone_boite_lettre)

        self.boite_au_lettre = QTextEdit()
        self.boite_au_lettre.setReadOnly(True)
        self.boite_au_lettre.setStyleSheet("background-color: white; color: black; font-size: 14px;")
        objet_gauche.addWidget(self.boite_au_lettre)

        layout.addLayout(objet_gauche, 1, 0)

        messagerie = QGroupBox("Messagerie")
        messagerie.setStyleSheet("QGroupBox { border: none; }")
        zone_messagerie = QVBoxLayout()
        zone_messagerie.addSpacing(15)
        destinataire = QHBoxLayout()
        self.combo = QComboBox()
        bouton_rafraichir_liste = QPushButton("rafraichir")
        bouton_rafraichir_liste.clicked.connect(self.rafraichir)
        destinataire.addWidget(QLabel("Pour:"))
        destinataire.addWidget(self.combo, 1)
        destinataire.addWidget(bouton_rafraichir_liste)
        zone_messagerie.addLayout(destinataire)

        self.zone_ecrire_message = QLineEdit()
        self.zone_ecrire_message.setPlaceholderText("Message...")
        zone_messagerie.addWidget(self.zone_ecrire_message)

        envoyer_message = QHBoxLayout()
        self.bouton_envoyer = QPushButton("Envoyer (Anonyme)")
        self.bouton_envoyer.clicked.connect(self.envoyer)

        self.zone_message_bien_envoye = QLabel("")
        self.zone_message_bien_envoye.setStyleSheet("color: green; font-weight: bold; margin-left: 10px;")

        envoyer_message.addWidget(self.bouton_envoyer)
        envoyer_message.addWidget(self.zone_message_bien_envoye)
        zone_messagerie.addLayout(envoyer_message)
        zone_messagerie.addStretch()

        messagerie.setLayout(zone_messagerie)
        layout.addWidget(messagerie, 1, 1)

        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 1)

        self.setLayout(layout)
        self.rafraichir()

    def afficher_message_recu(self, message):
        self.boite_au_lettre.append(f"message reçu : {message}")

    def rafraichir(self):
        if not self.client_logique: return
        self.combo.clear()
        clients = self.client_logique.liste_client_routeur("LISTE_CLIENT")
        for c in clients:
            if c['nom'] != f"CLIENT_{self.client_logique.pseudo}":
                clean = c['nom'].replace("CLIENT_", "")
                self.combo.addItem(f"{clean} ({c['ip']})", c)

    def envoyer(self):
        selection_destinataire = self.combo.currentIndex()
        if selection_destinataire == -1:
            QMessageBox.warning(self,"Attention","Veuillez choisir un destinataire")
            return

        destinataire = self.combo.itemData(selection_destinataire)
        message_texte = self.zone_ecrire_message.text()
        if len(message_texte) == 0:
            return

        liste_routeur = self.client_logique.liste_client_routeur("LISTE_ROUTER")
        if len(liste_routeur) == 0:
            QMessageBox.critical(self,"Erreur réseau","Aucun routeur trouvé votre message ne peut pas être anonyme")
            return

        nombre_routeur = len(liste_routeur)

# le vrai réseau TOR utilise 3 noeud donc ici 5 est largement suffisant et sinon les message mette très longtemp a arrivé
        if nombre_routeur < 5:
            maximum_saut = nombre_routeur
        else:
            maximum_saut = 5

        nombre_routeur_final = random.randint(1, maximum_saut)
        route = random.sample(liste_routeur, nombre_routeur_final)

        nom_des_routeur = []
        for routeur in route:
            nom_des_routeur.append(f"{routeur['nom']}")
        print(f"Route avec ({nombre_routeur_final} routeur -> {nom_des_routeur})")

        try:
            message_chiffre = self.client_logique.couche_onion(
                message_texte,
                route,
                destinataire['ip'],
                destinataire['port']
            )
            premier_routeur = route[0]
            socket_envoi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_envoi.connect((premier_routeur['ip'], premier_routeur['port']))
            socket_envoi.send(bytes(message_chiffre, 'utf-8'))
            socket_envoi.close()

            self.zone_ecrire_message.clear()
            self.zone_message_bien_envoye.setText("Message envoyé !")
            self.zone_message_bien_envoye.setStyleSheet("color: green; font-weight: bold; margin-left: 10px;")
            QTimer.singleShot(3000, lambda: self.zone_message_bien_envoye.setText(""))

        except Exception as e:
            print(f"Erreur lors de l'envoi : {e}")
            self.zone_message_bien_envoye.setText("Erreur envoi")
            self.zone_message_bien_envoye.setStyleSheet("color: red; font-weight: bold; margin-left: 10px;")

if __name__ == "__main__":
    client = QApplication(sys.argv)
    fenetre_graphique = FenetreConnexion()
    fenetre_graphique.show()
    sys.exit(client.exec())