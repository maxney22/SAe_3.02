import socket

def send_to_router(first_ip, first_port, next_ip, next_port, message):
    packet = f"{next_ip}:{next_port}:{message}"

    s = socket.socket()
    s.connect((first_ip, first_port))
    s.send(packet.encode())
    s.close()

if __name__ == "__main__":
    send_to_router(
        first_ip="127.0.0.1", first_port=15001,
        next_ip="127.0.0.1", next_port=15002,
        message="HELLO FROM CLIENT"
    )
