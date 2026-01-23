import socket
import threading

def ricevi(sock):
    while True:
        try:
            msg = sock.recv(1024)
            if not msg:
                print("Connessione chiusa dal server.")
                break
            print(msg)
        except:
            break

        

def main():
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(('localhost', 5000))

    username = input("Inserisci il tuo username")
    client.send(username.encode())

    print("Connesso al server!\nScrivi @utente messaggio per i privati.")

    threading.Thread(target=ricevi, args=(client)).start()

    while True:
        try:
            msg = input(">")
        except:
            break

if __name__ == "__main__":
    main()