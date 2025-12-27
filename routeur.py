import socket
import threading
import sys
import cryptage
import time

if len(sys.argv) < 3:
    print(f"Usage : python {sys.argv[0]} <IP_MASTER> <PORT_MASTER>")
    sys.exit(1)

master_ip = sys.argv[1]
master_port = int(sys.argv[2])
BLOC_TAILLE = 3 # variable pour cryptage
port = 0


def adresse_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def ping():
    while True:
        time.sleep(2)
        if port != 0:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((master_ip, master_port))
                s.send(bytes(f"PING|{port}", 'utf-8'))
                s.close()
            except:
                pass


def enregistrement():
    global port
    pub, priv = cryptage.generer_cles_automatiquement()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 0))
    port = s.getsockname()[1]
    print(f"ROUTEUR : {adresse_ip()}:{port}")
    threading.Thread(target=ping, daemon=True).start() # thread du ping

    try:
        s_reg = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_reg.connect((master_ip, master_port))
        msg = f"REG|ROUTER|{port}|{pub[0]}|{pub[1]}"
        s_reg.send(bytes(msg, 'utf-8'))
        s_reg.close()
        return s, priv
    except:
        sys.exit(1)


def routage(conn, priv):
    # merci root me pro
    try:
        gros_paquet = b""  # créer une variable en format bytes
        while True:
            paquet = conn.recv(4096)
            if not paquet:
                break
            gros_paquet += paquet

        paquet_texte = gros_paquet.decode('utf-8')
        if not paquet_texte: return

        paquet_filtre = ""
        for c in paquet_texte:
            # vérfie si dans le paquet il n'y a QUE soit des nombres ou des _ ou des ,
            if c.isdigit() or c == '_' or c == ',': # https://www.w3schools.com/python/ref_string_isdigit.asp
                paquet_filtre = paquet_filtre + c

        if "_" in paquet_filtre:
            liste_morceau = paquet_filtre.split('_')
        else:
            liste_morceau = paquet_filtre.split(',')

        conversion_paquet_int = []

        for morceau in liste_morceau:
            if len(morceau) > 0:
                nombre = int(morceau)
                conversion_paquet_int.append(nombre)

        message_dechiffre = cryptage.dechiffrer(conversion_paquet_int, priv, BLOC_TAILLE)
        if "|" not in message_dechiffre: return
        morceaux_message = message_dechiffre.split('|',1)
        if len(morceaux_message) != 2:
            return

        prochain_saut = morceaux_message[0]
        contenu_message = morceaux_message[1]

        if prochain_saut == "FINAL":
            info_destination = contenu_message.split(':',2)
            if len(info_destination) == 3:
                ip_destinataire = info_destination[0]
                port_destinataire = int(info_destination[1])
                message_final = info_destination[2]
                print(f"envoie destinataire -> {ip_destinataire}:{port_destinataire}")
                socket_envoi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                socket_envoi.connect((ip_destinataire, port_destinataire))
                socket_envoi.send(bytes(message_final, 'utf-8'))
                socket_envoi.close()
        else:
            info_prochain_saut = prochain_saut.split(':')
            ip_prochain_saut = info_prochain_saut[0]
            port_prochain_saut = int(info_prochain_saut[1])
            print(f"prochain saut -> {ip_prochain_saut}:{port_prochain_saut}")
            socket_envoi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_envoi.connect((ip_prochain_saut, port_prochain_saut))
            socket_envoi.send(bytes(contenu_message, 'utf-8'))
            socket_envoi.close()

    except Exception as e:
        print(f"erreur de routage {e}")
    finally:
        conn.close()


def start():
    sock, priv = enregistrement()
    sock.listen()
    while True:
        conn, _ = sock.accept()
        threading.Thread(target=routage, args=(conn, priv)).start()


if __name__ == "__main__":
    start()
