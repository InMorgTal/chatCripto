# Importa le librerie necessarie per la comunicazione via socket e il multithreading
import socket
import threading
import os
import json

#globali
my_iv = ""
chatPrivate={}

gruppo={}

username= ""

def riceviMsg(conn):
    buffer = ""

    while True:
        data = conn.recv(2048).decode()
        if not data:
            break  # connessione chiusa

        buffer += data

        while "\n" in buffer:
            msg_str, buffer = buffer.split("\n", 1)
            #pacchetto = json.loads(msg_str)  # pacchetto con iv, cPad, msgCifrato

            # Decifriamo il messaggio
            #iv = pacchetto["iv"]
            #cPad = pacchetto["cPad"]
            #msgCifrato = pacchetto["msgCifrato"]

            # Decifra la parte cifrata (devi avere la funzione decifra)
            #msg_decriptato_bytes = decifrare(load_aes_key('aes_key.bin'), iv, cPad, msgCifrato)
            #msg_decriptato_str = msg_decriptato_bytes.decode()  # da bytes a stringa
            msg = json.loads(msg_str)  # messaggio originale JSON

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
    #aes_key = load_aes_key()
    msg = (json.dumps(msg)+ "\n").encode()
    #iv, cPad, msgCifrato = cifrare(aes_key, msg)

# Mettiamo tutto in un dizionario
    #pacchetto = {
    #    "iv": iv,
    #    "cPad": cPad,
    #    "msgCifrato": msgCifrato
    #}

    #dati_da_inviare = json.dumps(pacchetto) + "\n"
    conn.sendall(msg.encode())

def menu(conn):
    global username
    while True:
        print("\n--- MENU ---")
        print("[1] Mostra lista chat")
        print("[2] Inizia conversazione privata")
        print("[3] Crea un gruppo")
        print("[4] Esci")

        scelta = input("Scegli un’opzione: ")

        match int(scelta):
            case 1:
                os.system('cls')
                caricaChat(conn)

            case 2:
                membri=[]
                while True:
                    user=input("Con chi vuoi parlare?\n")
                    if user != username:
                        break
                    print("Non puoi parlare con te stesso!")
                
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
    print("main attivato")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect(('localhost', 5000))
    print("inizioMandareAES")
    #mandare_AES_key(client)

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
