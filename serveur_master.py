"""
pour la connexion python mysql https://youtu.be/y3yNfHefu0Q?si=nStw_9cFNnj_mr3F
                                 https://www.geeksforgeeks.org/python/python-mysql/
                                 https://www.geeksforgeeks.org/python/python-mysql/

pour le python socket https://www.w3schools.com/python/ref_module_socket.asp
                      https://www.w3schools.com/python/ref_module_socketserver.asp

grosse GROSSE inspiration du code trouvé ici pour la partie socket du serveur https://www.datacamp.com/fr/tutorial/a-complete-guide-to-socket-programming-in-python
"""

import socket
import threading
import mysql.connector
import time
import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGroupBox, QFormLayout, QAbstractItemView,
                             QMessageBox)
from PyQt6.QtCore import QTimer, Qt


DB_CONFIG = {
    'host': '',
    'user': 'maxgui',
    'password': 'toto',
    'database': 'sae302'
}

def adresse_ip():
    try:
        socket_ip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_ip.connect(("8.8.8.8", 80))
        ip = socket_ip.getsockname()[0]
        socket_ip.close()
        return ip
    except:
        return "127.0.0.1"

def connexion_mariadb():
    return mysql.connector.connect(**DB_CONFIG)


def vider_table():
    conn = connexion_mariadb()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE routeur")
    conn.commit()
    conn.close()
    print("Table nettoye")


def enregistrement_noeud(nom, ip, port, n, e):
    conn = connexion_mariadb()
    cursor = conn.cursor()
    sql = """INSERT INTO routeur (nom, adresse_ip, port, cle_pub_n, cle_pub_e)
                VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY \
    UPDATE adresse_ip=%s, port=%s, cle_pub_n=%s, cle_pub_e=%s"""
    val = (nom, ip, port, str(n), str(e), ip, port, str(n), str(e))
    cursor.execute(sql, val)
    conn.commit()
    conn.close()
    print(f"nouveau noeud : {nom}")
    return True

def update_ping(ip, port):
    try:
        conn = connexion_mariadb()
        cursor = conn.cursor()
        sql = "UPDATE routeur SET ping = NOW() WHERE adresse_ip = %s AND port = %s"
        cursor.execute(sql, (ip, port))
        conn.commit()
        conn.close()
    except:
        pass

def nettoyage_db():
    while True:
        try:
            conn = connexion_mariadb()
            cursor = conn.cursor()
            sql = "DELETE FROM routeur WHERE ping < (NOW() - INTERVAL 5 SECOND)"
            cursor.execute(sql)
            conn.commit()
            conn.close()
        except:
            pass
        time.sleep(1)

def recuperer_noeuds_par_prefixe(prefixe):
    chaine = ""
    try:
        conn = connexion_mariadb()
        cursor = conn.cursor()
        like_query = f"{prefixe}%"
        sql = "SELECT nom, adresse_ip, port, cle_pub_n, cle_pub_e FROM routeur WHERE nom LIKE %s"
        cursor.execute(sql, (like_query,))
        rows = cursor.fetchall()
        segments = []
        for row in rows:
            seg = f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}"
            segments.append(seg)
        chaine = ";".join(segments)
        conn.close()
    except:
        pass
    return chaine


def gestion_client_routeur(socket_commande, adresse_client_routeur):
# trois commande possible soit PING, ENRE ou LISTE_CLIENT ou LISTE_ROUTEUR
    try:
        paquet = socket_commande.recv(8192).decode('utf-8')
        if not paquet:
            return

        info_client_routeur = paquet.split('|')
        commande = info_client_routeur[0]

        if commande.startswith("PING"):
            if len(info_client_routeur) >= 2:
                port_ping = int(info_client_routeur[1])
                update_ping(adresse_client_routeur[0], port_ping)

        elif commande.startswith("ENRE"):
            type_noeud = info_client_routeur[1]

            if type_noeud == "ROUTER":
                port_routeur = int(info_client_routeur[2])
                nom_routeur = f"ROUTER_{adresse_client_routeur[0]}_{port_routeur}"
                cle_n = info_client_routeur[3]
                cle_e = info_client_routeur[4]

                enregistrement_db = enregistrement_noeud(nom_routeur, adresse_client_routeur[0], port_routeur, cle_n, cle_e)

                if enregistrement_db:
                    socket_commande.send("OK".encode('utf-8'))
                else:
                    socket_commande.send("ERR".encode('utf-8'))

            elif type_noeud == "CLIENT":
                pseudo_client = info_client_routeur[2]
                port_client = int(info_client_routeur[3])
                nom_client = f"CLIENT_{pseudo_client}"
                cle_n = info_client_routeur[4]
                cle_e = info_client_routeur[5]

                enregistrement_db = enregistrement_noeud(nom_client, adresse_client_routeur[0], port_client, cle_n, cle_e)

                if enregistrement_db:
                    socket_commande.send("OK".encode('utf-8'))
                else:
                    socket_commande.send("ERR".encode('utf-8'))

        elif commande == "LISTE_ROUTER":
            liste_routeurs = recuperer_noeuds_par_prefixe("ROUTER_")
            socket_commande.send(liste_routeurs.encode('utf-8'))

        elif commande == "LISTE_CLIENT":
            liste_clients = recuperer_noeuds_par_prefixe("CLIENT_")
            socket_commande.send(liste_clients.encode('utf-8'))

    except Exception as e:
        print(f"Erreur gestion client : {e}")
    finally:
        socket_commande.close()


def demarrage_master():
    global port_ecoute
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', port_ecoute))
        server.listen()
        vider_table()
        threading.Thread(target=nettoyage_db, daemon=True).start()
        while True:
            conn, addr = server.accept()
            threading.Thread(target=gestion_client_routeur, args=(conn, addr)).start()
    except OSError as e:
        print(f"Erreur fatale socket (probablement port déjà pris): {e}")


class FenetreConfig(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuration Serveur")
        self.resize(400, 200)
        self.ip_locale = adresse_ip()

        layout = QVBoxLayout()

        titre = QLabel("Paramètres de Démarrage")
        titre.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titre)

        form = QFormLayout()

        self.zone_ip = QLabel(self.ip_locale)
        self.zone_ip.setStyleSheet("color: gray; font-style: italic;")

        self.port_master = QLineEdit("")
        self.port_master.setPlaceholderText("Ex: 20000")

        self.adresse_ip_DB = QLineEdit(DB_CONFIG['host'])
        self.adresse_ip_DB.setPlaceholderText("Ex: localhost ou 192.168.x.x")

        form.addRow("Mon IP locale:", self.zone_ip)
        form.addRow("Port d'écoute:", self.port_master)
        form.addRow("IP Database:", self.adresse_ip_DB)

        layout.addLayout(form)

        self.bouton_lancer = QPushButton("Lancer le Serveur")
        self.bouton_lancer.setStyleSheet("font-weight: bold; padding: 8px;")
        self.bouton_lancer.clicked.connect(self.lancer)
        layout.addWidget(self.bouton_lancer)

        self.setLayout(layout)


    def lancer(self):
        global port_ecoute

# erreur sur le port
        try:
            p = int(self.port_master.text())
            if p < 10000 or p > 65535:
                raise ValueError
            port_ecoute = p
        except ValueError:
            QMessageBox.warning(self, "Attention port","Préférer un port entre 10000 et 65535 sinon risque de collision avec d'autre services")
            return

# erreur sur l'adresse ip
        ip_bdd = self.adresse_ip_DB.text()
        if not ip_bdd:
            QMessageBox.warning(self, "Attention", "Veuillez entrer une adresse IP pour la base de données")
            return
        DB_CONFIG['host'] = ip_bdd

# erreur connexion mysql
        try:
            test_conn = mysql.connector.connect(**DB_CONFIG)
            test_conn.close()
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erreur de Connexion BDD",
                                 f"Impossible de se connecter à la base de données !\n\n"
                                 f"Vérifiez :\n"
                                 f"1. L'adresse IP ({ip_bdd}), si vous avez taper localhost et que ça na pas fonctionner essayer 127.0.0.1\n"
                                 f"2. Que MariaDB est bien lancé\n\n"
                                 f"Détail technique : {err}")
            return
        QMessageBox.information(self, "Connecté", "Le serveur est connecté la base de données")
        self.fen_tableau = FenetreTableau()
        self.fen_tableau.show()
        self.close()


class FenetreTableau(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serveur Master")
        self.resize(800, 500)
        threading.Thread(target=demarrage_master, daemon=True).start()
        layout = QVBoxLayout()

        self.zone_info_master = QLabel(f"Serveur Master --> IP: {adresse_ip()} PORT: {port_ecoute}")
        self.zone_info_master.setStyleSheet(
            "background-color: LightGreen; color: green; border: 1px solid #c3e6cb; padding: 10px; font-weight: bold; font-size: 14px;")
        self.zone_info_master.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zone_info_master.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.zone_info_master)

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Nom", "IP", "Port", "Clé N", "Clé E", "Dernier ping"])
        haut_page = self.table.horizontalHeader()
        haut_page.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.bouton_supprimer = QPushButton("Supprimer le nœud sélectionné")
        self.bouton_supprimer.setStyleSheet("background-color: #ffcccc; color: red; font-weight: bold;")
        self.bouton_supprimer.clicked.connect(self.supprimer_noeud)
        layout.addWidget(self.bouton_supprimer)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.charger_donnees_bdd)
        self.timer.start(1000)

    def charger_donnees_bdd(self):
        try:
            conn = connexion_mariadb()
            cursor = conn.cursor()
            cursor.execute("SELECT nom, adresse_ip, port, cle_pub_n, cle_pub_e, ping FROM routeur")
            rows = cursor.fetchall()
            conn.close()

            ligne_selectionnee = self.table.currentRow()

            self.table.setRowCount(0)
            for row_number, row_data in enumerate(rows):
                self.table.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row_number, column_number, item)

            if ligne_selectionnee != -1 and ligne_selectionnee < self.table.rowCount():
                self.table.selectRow(ligne_selectionnee)

        except Exception:
            pass

    def supprimer_noeud(self):
        ligne = self.table.currentRow()
        if ligne == -1:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une ligne.")
            return

        item = self.table.item(ligne, 0)
        if not item: return
        nom = item.text()

        confirmation = QMessageBox.question(self, "Confirmer", f"Supprimer {nom} ?",QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirmation == QMessageBox.StandardButton.Yes:
            try:
                conn = connexion_mariadb()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM routeur WHERE nom = %s", (nom,))
                conn.commit()
                conn.close()
                self.charger_donnees_bdd()
                QMessageBox.information(self, "Succès", "Nœud supprimé.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur SQL : {e}")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    fen_config = FenetreConfig()
    fen_config.show()
    sys.exit(app.exec())