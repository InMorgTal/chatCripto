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
    global username
    msg={
    "tipo": "caricaChat",
    "sorgente":username,
    }
    inviaMsg(conn,msg)
  


def inviaMsg(conn,msg):
    
    conn.sendall((json.dumps(msg)+ "\n").encode())  

def menu(conn):
    global username
    while True:
        print("\n--- MENU ---")
        print("1) Mostra lista chat")
        print("2) Inizia conversazione privata")
        print("3) Crea un gruppo")
        print("4) Esci")

        scelta = input("Scegli un’opzione: ")

        match int(scelta):
            case 1:
                os.system('cls')
                caricaChat(conn)

            case 2:
                membri=[]
                user=input("Con chi vuoi parlare?\n")
                membri.append(username)
                membri.append(user)
                inviaMsg(conn,{"tipo":"iniziaConv","membri":membri})
            case 3:
                membri=[]
                while True:
                    
                    user=input("Inserisci partecipanti (0 per terminare selezione)")
                    if user != "0":
                        membri.append(user)
                    else:
                        break
                    
                membri.append(username)
                inviaMsg(conn,{"tipo":"creaGruppo","membri":membri})


def main():
    global username
    """
    Inizializza la connessione al server e gestisce l'input dell'utente.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect(('localhost', 5000))

    print("Connesso al server!\n")

    while True:
        username = input("Inserisci username\n")
        if len(username)>3:
            break
        print("Troppo corto")

    msg = {"username":username}
    inviaMsg(client,msg)

    t = threading.Thread(target=riceviMsg, args=(client,))
    t.start()
    menu(client)
    

        










if __name__ == "__main__":
    main()
