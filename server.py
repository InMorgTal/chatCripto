'''Implementare una chat client server con Thread che sia in grado di gestire lo scambio di messaggi sia in Broadcast che Unicast.
l'utente("Client") deve poter scrivere il proprio Username in un dizionario gestito dal server ed essere quindi in grado sia di inviare messaggi a singoli client
(inserendo l'user destinatario con la seguente dicitura @user ) che in broadcast.
'''


import socket
import threading


sServer=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sServer.bind(('localhost', 5000))

sServer.listen()

# username : socket
utenti = {} 




def gestisci_client(conn, addr):
    
    username = conn.recv(1024).decode().strip()
    utenti[username] = conn#vogliamo associare a ogni username la relativa socket del client connesso

    
    while True:
        try:
            msg = conn.recv(1024).decode()
            if not msg:
                break

            # messaggio privato
            if msg.startswith("@"):
                try:
                    parti = msg.split(" ", 1)  # divide in massimo 2 parti

                    if len(parti) < 2:
                        conn.sendall("Formato non valido. Usa: @destinatario messaggio\n".encode())
                        continue


                    dest = parti[0][1:]  # rimuove la @ e prende il nome

                    msg = parti[1]#prendere il nome dopo la chiocciola e metterlo nel dizionario e inviare messaggio a connessione associata ad esso

                    if dest in utenti:
                        utenti[dest].sendall(f"[{username} a te ]: {msg}".encode())
                    else:
                        conn.sendall(f"Utente '{dest}' non trovato\n".encode())

                except ValueError:
                    conn.sendall("Formato non valido. Usa: @destinatario messaggio\n".encode())

            else:
                # messaggio broadcast
                for c in utenti.values():
                    if c != conn:
                        c.sendall(f"[{username} a tutti ]:  {msg}".encode())
           

        except:
            break

    # 4. Disconnessione
    print(f"[-] {username} disconnesso")
    del utenti[username]
    conn.close()






def main():


    print("Server con dizionario attivo sulla porta 5000")

    while True:
        conn, addr = sServer.accept()
        threading.Thread(target=gestisci_client, args=(conn, addr)).start()


if __name__ == "__main__":
    main()