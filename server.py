'''Implementare una chat client server con Thread che sia in grado di gestire lo scambio di messaggi sia in Broadcast che Unicast.
l'utente("Client") deve poter scrivere il proprio Username in un dizionario gestito dal server ed essere quindi in grado sia di inviare messaggi a singoli client
(inserendo l'user destinatario con la seguente dicitura @user ) che in broadcast.
'''

# Importa le librerie necessarie per la comunicazione via socket e il multithreading
import socket
import threading

# Crea un socket server TCP/IP per accettare connessioni dai client
sServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Lega il server all'indirizzo localhost e alla porta 5000
sServer.bind(('localhost', 5000))

# Mette il server in ascolto per accettare connessioni in arrivo
sServer.listen()

# Dizionario che memorizza gli utenti connessi: {username: socket_del_client}
# Viene usato per le comunicazioni broadcast e unicast
utenti = {}


# Funzione che gestisce ogni client connesso al server
# Viene eseguita in un thread separato per ogni client
def gestisci_client(conn, addr):
    """
    Gestisce la comunicazione con un singolo client.
    - Riceve l'username del client
    - Verifica che non sia già occupato
    - Riceve e elabora i messaggi (broadcast o privati)
    """

    # Loop per richiedere l'username finché non è disponibile
    while True:
        # Riceve l'username dal client (massimo 1024 byte) e lo decodifica
        username = conn.recv(1024).decode().strip()
        
        # Controlla se l'username è già stato registrato
        if username not in utenti:
            # Se non esiste, esce dal loop e registra l'utente
            break
        
        # Se l'username è già occupato, invia un messaggio d'errore al client
        conn.sendall("Username occupato scegline un altro\n".encode())

    # Stampa un messaggio di conferma nel log del server
    print((f"aggiunto utente: {username}"))
    
    # Associa l'username del client alla sua socket nel dizionario
    # Questo permette di inviare messaggi privati e broadcast a questo client
    utenti[username] = conn

    # Loop principale: gestisce tutti i messaggi inviati dal client
    while True:
        try:
            # Riceve il messaggio dal client, lo decodifica e rimuove spazi/newline
            msg = conn.recv(1024).decode().strip()
            
            # Se il messaggio è vuoto, il client si è disconnesso
            if not msg:
                break

            # Controlla se il messaggio è privato (inizia con @)
            if msg.startswith("@"):
                try:
                    # Divide il messaggio in massimo 2 parti: ["@destinatario", "testo del messaggio"]
                    parti = msg.split(" ", 1)

                    # Controlla che il formato sia corretto (@ e messaggio)
                    if len(parti) < 2:
                        conn.sendall("Formato non valido. Usa: @destinatario messaggio\n".encode())
                        continue

                    # Estrae il nome del destinatario rimuovendo il simbolo @
                    dest = parti[0][1:]

                    # Estrae il testo del messaggio (la seconda parte)
                    msg = parti[1]

                    # Verifica che il destinatario esista e non sia se stesso
                    if dest in utenti and dest != username:
                        # Invia il messaggio privato al destinatario
                        utenti[dest].sendall(f"[{username} (in privato) ]: {msg}".encode())
                    else:
                        # Se il destinatario non esiste, invia un messaggio d'errore
                        conn.sendall(f"Impossibile inviare il messaggio\n".encode())

                except ValueError:
                    # Se c'è un errore nel parsing, segnala il formato non valido
                    conn.sendall("Formato non valido. Usa: @destinatario messaggio\n".encode())

            else:
                # Messaggio broadcast: invia a tutti gli altri client
                # Itera attraverso tutte le socket dei client connessi
                for c in utenti.values():
                    # Invia il messaggio solo agli altri client, non al mittente
                    if c != conn:
                        c.sendall(f"[{username}]:  {msg}".encode())

        except:
            # Se c'è un errore durante la ricezione del messaggio, esce dal loop
            break

    # Fase di disconnessione: pulizia quando il client si disconnette
    print(f"[-] {username} disconnesso")
    
    # Rimuove l'utente dal dizionario dei client connessi
    del utenti[username]
    
    # Chiude la socket del client
    conn.close()


# Funzione principale che avvia il server e accetta connessioni
def main():
    """
    Avvia il server e rimane in ascolto per accettare connessioni dai client.
    Per ogni client che si connette, crea un thread separato che lo gestisce.
    """

    # Stampa un messaggio di avvio del server
    print("Server attivo e in ascolto...")

    # Loop infinito: accetta continuamente nuove connessioni dai client
    while True:
        # Accetta una nuova connessione dal client
        # conn = socket del client connesso
        # addr = indirizzo IP e porta del client
        conn, addr = sServer.accept()
        
        # Stampa un messaggio di conferma con l'indirizzo del client connesso
        print(f"[+] Connessione da {addr}")
        
        # Crea un nuovo thread per gestire questo client
        # target = funzione da eseguire nel thread (gestisci_client)
        # args = argomenti da passare alla funzione (conn e addr)
        # .start() = avvia il thread
        threading.Thread(target=gestisci_client, args=(conn, addr)).start()


# Punto di ingresso del programma
if __name__ == "__main__":
    main()