'''Implementare una chat client server con Thread che sia in grado di gestire lo scambio di messaggi sia in Broadcast che Unicast.
l'utente("Client") deve poter scrivere il proprio Username in un dizionario gestito dal server ed essere quindi in grado sia di inviare messaggi a singoli client
(inserendo l'user destinatario con la seguente dicitura @user ) che in broadcast.
'''


import socket
import threading


server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(('localhost', 12345))


# Dizionario: username → socket
utenti = {}   #  "mario": <socket di mario>,
              #  "anna": <socket di anna>




def gestisci_client(conn, addr):
    # 1. Il primo messaggio ricevuto è lo username
    username = conn.recv(1024).decode().strip()
    utenti[username] = conn#vogliamo associare a ogni username la relativa socket del client connesso

    
    while True:
        try:
            msg = conn.recv(1024).decode()
            if not msg:
                break

            # 2. Messaggio privato del tipo: @mario ciao!
            if msg.startswith("@"):
                try:
                   

                except ValueError:
                    conn.send("Formato non valido. Usa: @destinatario messaggio\n".encode())

            else:
                # 3. Messaggio in broadcast
                for c in utenti.values():
                    if c != conn:
                        c.send(f"[{username}] {msg}".encode())
            #for nome, sock in utenti.items():
                #if sock != conn:
                    #sock.send(f"[{username}] {msg}".encode())

        except:
            break

    # 4. Disconnessione
    print(f"[-] {username} disconnesso")
    del utenti[username]
    conn.close()






def main():


    print("Server con dizionario attivo sulla porta 5000")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=gestisci_client, args=(conn, addr)).start()


if __name__ == "__main__":
    main()