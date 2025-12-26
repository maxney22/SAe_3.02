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
BLOC_TAILLE = 3
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
    """Envoie un PING au master toutes les 10 secondes"""
    while True:
        time.sleep(10)
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
    try:
        data = conn.recv(16384).decode('utf-8')
        if not data: return

        clean_data = "".join([c for c in data if c.isdigit() or c in ['_', ',']])
        if "_" in clean_data:
            parts = clean_data.split('_')
        else:
            parts = clean_data.split(',')
        cipher_ints = [int(p) for p in parts if p]

        decrypted = cryptage.dechiffrer(cipher_ints, priv, BLOC_TAILLE)
        if "|" not in decrypted: return
        hop, payload = decrypted.split('|', 1)

        if hop == "FINAL":
            dest_ip, dest_port, msg = payload.split(':', 2)
            print(f"[LIVRAISON] -> {dest_ip}:{dest_port}")
            out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            out.connect((dest_ip, int(dest_port)))
            out.send(bytes(msg, 'utf-8'))
            out.close()
        else:
            next_ip, next_port = hop.split(':')
            print(f"[RELAI] -> {next_ip}:{next_port}")
            out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            out.connect((next_ip, int(next_port)))
            out.send(bytes(payload, 'utf-8'))
            out.close()

    except Exception as e:
        print(f"[ERREUR ROUTAGE] {e}")
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
