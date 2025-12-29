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

# --- CONFIGURATION BDD ---
DB_CONFIG = {
    'host': '10.128.200.61',
    'user': 'maxgui',
    'password': 'toto',
    'database': 'sae302'
}

port_ecoute = int(input("choisir le port d'écoute (conseiller au dessus de 20000) : "))


def connexion_mariadb():
    return mysql.connector.connect(**DB_CONFIG)


def vider_table():
    try:
        conn = connexion_mariadb()
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE routeur")
        conn.commit()
        conn.close()
        print("[INFO] Table nettoye (TRUNCATE).")
    except Exception as e:
        print(f"[ERREUR] Reset table : {e}")


def enregistrement_noeud(nom, ip, port, n, e):
    try:
        conn = connexion_mariadb()
        cursor = conn.cursor()
        sql = """INSERT INTO routeur (nom, adresse_ip, port, cle_pub_n, cle_pub_e)
                 VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY \
        UPDATE adresse_ip=%s, port=%s, cle_pub_n=%s, cle_pub_e=%s"""
        val = (nom, ip, port, str(n), str(e), ip, port, str(n), str(e))
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        print(f"[+] Enregistre/Update : {nom}")
        return True
    except Exception as err:
        print(f"[ERREUR] SQL Register : {err}")
        return False


def update_ping(ip, port):
    """Met a jour le timestamp last_seen quand on recoit un PING"""
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
    """Tourne en boucle pour supprimer les noeuds inactifs > 15 sec"""
    while True:
        try:
            conn = connexion_mariadb()
            cursor = conn.cursor()
            # Supprime ceux qui n'ont pas ping depuis 15 secondes
            sql = "DELETE FROM routeur WHERE ping < (NOW() - INTERVAL 15 SECOND)"
            cursor.execute(sql)
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_count > 0:
                print(f"[-] NETTOYAGE : {deleted_count} noeud(s) mort(s) supprime(s) de la BDD.")
        except Exception as e:
            print(f"[ERREUR] Nettoyage : {e}")

        time.sleep(5)


def recuperer_noeuds_par_prefixe(prefixe):  # https://www.w3schools.com/python/ref_string_join.asp
    chaine = ""
    try:
        conn = connexion_mariadb()
        cursor = conn.cursor()
        like_query = f"{prefixe}%"
        sql = "SELECT nom, adresse_ip, port, cle_pub_n, cle_pub_e FROM routeur WHERE nom LIKE %s"
        cursor.execute(sql, (like_query,))
        rows = cursor.fetchall()
        segments = []
        for row in rows:   # formatage
            seg = f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}"
            segments.append(seg)
        chaine = ";".join(segments)
        conn.close()
    except Exception as err:
        print(f"[ERREUR] SQL Select : {err}")
    return chaine


def gestion_client(conn, addr):   # https://www.w3schools.com/python/ref_string_startswith.asp
    try:
        data = conn.recv(8192).decode('utf-8')
        if data.startswith("PING|"):
            parts = data.split('|')
            port_ping = int(parts[1])
            update_ping(addr[0], port_ping)

        elif data.startswith("REG|"):
            parts = data.split('|')
            type_node = parts[1]
            if type_node == "ROUTER":
                r_port = int(parts[2])
                nom = f"ROUTER_{addr[0]}_{r_port}"
                n, e = parts[3], parts[4]
                if enregistrement_noeud(nom, addr[0], r_port, n, e):
                    conn.send("OK".encode('utf-8'))
                else:
                    conn.send("ERR".encode('utf-8'))
            elif type_node == "CLIENT":
                pseudo = parts[2]
                c_port = int(parts[3])
                nom = f"CLIENT_{pseudo}"
                n, e = parts[4], parts[5]
                if enregistrement_noeud(nom, addr[0], c_port, n, e):
                    conn.send("OK".encode('utf-8'))
                else:
                    conn.send("ERR".encode('utf-8'))

        elif data == "GET_ROUTERS":
            conn.send(recuperer_noeuds_par_prefixe("ROUTER_").encode('utf-8'))

        elif data == "GET_CLIENTS":
            conn.send(recuperer_noeuds_par_prefixe("CLIENT_").encode('utf-8'))

    except Exception as e:
        pass
    finally:
        conn.close() # très important pour éviter les connexions fantôme


def demarrage_master():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port_ecoute))
    server.listen()

    vider_table()
    print(f"--- SERVEUR MASTER EN LIGNE SUR PORT {port_ecoute} ---")

    # Thread nettoyage
    threading.Thread(target=nettoyage_db, daemon=True).start()

    while True:
        conn, addr = server.accept()
        # Thread gestion des clients
        threading.Thread(target=gestion_client, args=(conn, addr)).start()


if __name__ == "__main__":
    demarrage_master()
