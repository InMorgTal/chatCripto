# Importa le librerie necessarie per la comunicazione via socket e il multithreading
import socket
import threading
import os
import json



chatPrivate={}
gruppo={}


username= ""

def riceviMsg(conn):

    buffer = ""

    while True:
        data = conn.recv(2048).decode()
        if not data:
            break

        buffer += data

        while "\n" in buffer:
            msg_str, buffer = buffer.split("\n", 1)
            msg = json.loads(msg_str)
    match msg["tipo"]:
        case "caricaChat":
            for nomechat in msg["chat"]:
                print(nomechat)




def caricaChat(conn):
     
    msg={
    "tipo": "caricaChat",
    "sorgente":username,
    }
    inviaMsg(conn,msg)
  


def inviaMsg(conn,msg):
    
    conn.sendall((json.dumps(msg)+ "\n").encode())  

def menu(conn):
    
    while True:
    
    os.system('cls')

    for i in range(len):
        print()



def main():
    """
    Inizializza la connessione al server e gestisce l'input dell'utente.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect(('localhost', 5000))

    print("Connesso al server!\n")

    username=input("Inserisci username")

    msg = {"username":username}
    inviaMsg(client,msg)

    t = threading.Thread(target=riceviMsg, args=(client,))
    t.start()

    menu(client)

        










if __name__ == "__main__":
    main()
