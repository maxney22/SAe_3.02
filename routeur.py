import socket
import threading

def make_handle(conn):
    def wrapped():
        try:
            data = conn.recv(4096)
            if not data:
                conn.close()
                return

            message = data.decode()
            print(f"[ROUTER] Reçu brut : {message}")
            parts = message.split(":", 2)

            if len(parts) < 3:
                print("[ROUTER] ERREUR : format invalide")
                conn.close()
                return

            next_host = parts[0]
            next_port = int(parts[1])
            real_message = parts[2]

            print(f"[ROUTER] Next hop = {next_host}:{next_port}")
            print(f"[ROUTER] Vrai message = {real_message}")

            # Envoi au prochain routeur
            out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            out.connect((next_host, next_port))
            out.sendall(real_message.encode())
            out.close()

            print(f"[ROUTER] Message transmis à {next_port}")

            conn.close()

        except Exception as e:
            print(f"[ROUTER] Erreur : {e}")
            conn.close()

    return wrapped


def router(listen_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", listen_port))
    s.listen()

    print(f"[ROUTER {listen_port}] Fantôme à l’affût…")

    while True:
        conn, addr = s.accept()
        t = threading.Thread(target=make_handle(conn))
        t.start()


if __name__ == "__main__":
    LISTEN_PORT = 15001
    router(LISTEN_PORT)
