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

            msg = sock.recv(1024).decode().strip()

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
            break

def main():
    """
    Inizializza la connessione al server e gestisce l'input dell'utente.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect(('localhost', 5000))

    print("Connesso al server!\nScrivi @utente messaggio per i privati.")

    username = input("Inserisci il tuo username: ")

    client.sendall(username.encode())
    
    threading.Thread(target=ricevi, args=(client,)).start()


    while True:
        try:

            msg = input(">")
            client.sendall(msg.encode())
        except:
            break

if __name__ == "__main__":
    main()
