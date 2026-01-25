# Importa le librerie necessarie per la comunicazione via socket e il multithreading
import socket
import threading

# Funzione che gestisce la ricezione dei messaggi dal server in un thread separato
def ricevi(sock):
    """
    Riceve continuamente messaggi dal server e li stampa.
    Esegue in un thread separato per non bloccare l'input dell'utente.
    """
    while True:
        try:
            # Riceve il messaggio dal server (massimo 1024 byte), lo decodifica e rimuove spazi/newline
            msg = sock.recv(1024).decode().strip()
            
            # Se il messaggio è vuoto, significa che il server ha chiuso la connessione
            if not msg:
                print("Connessione chiusa dal server.")
                break
            
            # \r ritorna all'inizio della riga, sovrascrivendo la freccetta precedente
            # e stampa il messaggio ricevuto
            print("\r" + msg)  
            
            # Ristampa la freccetta (prompt) senza andare a capo
            # flush=True forza la visualizzazione immediata sullo schermo
            print(">", end="", flush=True)
        except:
            # Se ci sono errori durante la ricezione, esce dal loop
            break

        
# Funzione principale che gestisce la connessione e l'invio dei messaggi
def main():
    """
    Inizializza la connessione al server e gestisce l'input dell'utente.
    """
    
    # Crea un socket TCP/IP per la comunicazione client-server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Si connette al server in localhost sulla porta 5000
    client.connect(('localhost', 5000))
    
    # Stampa un messaggio di benvenuto con le istruzioni
    print("Connesso al server!\nScrivi @utente messaggio per i privati.")
    
    # Chiede all'utente di inserire il proprio username
    username = input("Inserisci il tuo username: ")
    
    # Invia lo username al server (codificato in bytes)
    client.sendall(username.encode())

    # Avvia un thread separato per ricevere i messaggi dal server
    # Così l'utente può continuare a scrivere messaggi senza blocchi
    threading.Thread(target=ricevi, args=(client,)).start()

    # Loop principale: legge l'input dell'utente e lo invia al server
    while True:
        try:
            # Stampa il prompt ">" e aspetta l'input dell'utente
            msg = input(">")
            
            # Invia il messaggio al server (codificato in bytes)
            client.sendall(msg.encode())
        except:
            # Se ci sono errori durante l'invio, esce dal loop
            break

# Punto di ingresso del programma
if __name__ == "__main__":
    main()