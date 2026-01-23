import socket
import threading

def ricevi(sock):
    while True:
        try:
            msg = sock.recv(1024)
            if not msg:
                print("Connessione chiusa dal server.")
                break
            
        except:
            break

def main():
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect

    username = input
    client.send(username.encode())

    print("Connesso al server!\nScrivi @utente messaggio per i privati.")

    threading.Thread

    while True:
        try:
            msg = 
        except:
            break

if __name__ == "__main__":
    main()