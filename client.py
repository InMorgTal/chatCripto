# Importa le librerie necessarie per la comunicazione via socket e il multithreading
import socket
import threading
import os
import json


chat ={
    "privata":{},
    "gruppo":{}
} 

def ricevi(conn):
    """
    Riceve continuamente messaggi dal server e li stampa.
    Esegue in un thread separato per non bloccare l'input dell'utente.
    """
    os.system('cls')
    while True:
            msg = conn.recv(2048).decode().strip()
            msg = json.loads(msg)




          
            
           


def invia(conn):

    os.system('cls')











def main():
    """
    Inizializza la connessione al server e gestisce l'input dell'utente.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect(('localhost', 5000))

    print("Connesso al server!\n")

    t = threading.Thread(target=ricevi, args=(client,))
    t.start()
    invia(client)
        










if __name__ == "__main__":
    main()
