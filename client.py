# Importa le librerie necessarie per la comunicazione via socket e il multithreading
import socket
import threading
import os
import json


chat ={
    "privata":{},
    "gruppo":{}
} 


username=""




def ricevi(conn):
    while True:
            msg = conn.recv(2048).decode().strip()
            msg = json.loads(msg)




          
            
           


def menu(conn):
    os.system('cls')

    for i in len(chat)






def caricaChat(conn):
     
    msg={
    "tipo": "caricaChat",
    "sorgente":username
    }
    invia(conn,msg)
  


def invia(conn,msg):
    
    conn.sendall((json.dumps(msg)+ "\n").encode())  
 






def main():
    """
    Inizializza la connessione al server e gestisce l'input dell'utente.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect(('localhost', 5000))

    print("Connesso al server!\n")

    t = threading.Thread(target=ricevi, args=(client,))
    t.start()

    caricaChat(client) 
    menu(client)
        










if __name__ == "__main__":
    main()
