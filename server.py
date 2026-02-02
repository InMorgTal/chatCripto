import socket
import threading
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
import json


sServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sServer.bind(('localhost', 5000))

sServer.listen(20)

gruppi={} 

chatPrivate={}

utenti = {}


def riceviMsg(conn):
    global utenti
    buffer = ""

    while True:
        data = conn.recv(2048).decode()
        if not data:
            break  # connessione chiusa

        buffer += data

        while "\n" in buffer:
            msg_str, buffer = buffer.split("\n", 1)
            pacchetto = json.loads(msg_str)  # pacchetto con iv, cPad, msgCifrato

            # Decifriamo il messaggio
            ##iv = pacchetto["iv"]
            ##cPad = pacchetto["cPad"]
            ##msgCifrato = pacchetto["msgCifrato"]

            # Decifra la parte cifrata (devi avere la funzione decifra)
            ##msg_decriptato_bytes = decifrare(utenti[conn][1], iv, cPad, msgCifrato)
            ##msg_decriptato_str = msg_decriptato_bytes.decode()  # da bytes a stringa
            ##msg = json.loads(msg_decriptato_str)  # messaggio originale JSON

            return msg

def inviaMsg(conn,msg):
    global utenti
    msg=(json.dumps(msg)+ "\n").encode()
    ##iv, cPad, msgCifrato = cifrare(utenti[conn][1], msg)

    # Mettiamo tutto in un dizionario
    ##pacchetto = {
    ##    "iv": iv,
    ##    "cPad": cPad,
    ##    "msgCifrato": msgCifrato
    ##}

    ##dati_da_inviare = json.dumps(pacchetto) + "\n"
##########################################################################################
    conn.sendall(dati_da_inviare.encode())

def creaChiaveChatPrivata(utente1,utente2):       
    nomi=[utente1,utente2]                                      #mi serve una chiave per il dizionario delle chat private e quindi uso i due username ordinati
    return tuple(sorted(nomi))                                              #in modo da essere semre nello stesso ordine dato che potrebbero essere sia in sorgente che destinazione

def messaggio(msg):
    if msg["destinazione"] in gruppi:                                                   #invio messaggio gruppo
        gruppi[msg["destinazione"]]["messaggi"].append(msg)
        for username in gruppi["membri"]:
            if username != msg["sorgente"]:
                inviaMsg(utenti[username],msg)
    else:
        chiavePrivata=creaChiaveChatPrivata(msg["sorgente"],msg["destinazione"])        #invio messaggio privata
        chatPrivate[chiavePrivata]["messaggi"].append(msg)
        for username in chatPrivate[chiavePrivata]["membri"]:
            if username != msg["sorgente"]:
                inviaMsg(utenti[username],msg)

def creaGruppo(msg):
    if msg["destinazione"] not in gruppi:                                               #creo gruppo
        gruppi[msg["destinazione"]]={
        "membri":[msg["membri"]],
        "messaggi":[]
    }
    
def iniziaConversazione(msg):                                                           #creo chat privata
    chiaveChat=creaChiaveChatPrivata(msg["membri"][0],msg["membri"][1])
    chatPrivate [chiaveChat]={
        "membri":[msg["membri"][0],msg["membri"][1]],
        "messaggi":[]
    }

def caricaChat(conn,msg):
    username_cercato = msg["sorgente"]
    chat=[]
    for gruppo, info in gruppi.items():
        if username_cercato in info["membri"]:
            chat.append(gruppo)
    for private, info in chatPrivate.items():
        if username_cercato in info["membri"]:
            chat.append(private)

    msg={
        "tipo":"caricaChat",
        "destinazione":username_cercato,
        "chat":chat
    }
    inviaMsg(conn,msg)

'''



    for gruppo, info in gruppi.items():
        if username_cercato in info["membri"]:
            print(f"{username_cercato} è presente in {gruppo}")
            inviaMsg(utenti[username_cercato],info["messaggi"][-20:])
        
    for chat, info in chatPrivate.items():
        if username_cercato in info["membri"]:
            print(f"{username_cercato} è presente nella chat privata {chat}")
            inviaMsg(utenti[username_cercato],info["messaggi"][-20:])
'''
def inviaMsg(conn,msg):

    conn.sendall((json.dumps(msg)+ "\n").encode())  

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
        return msg

def gestisciClient(conn):
    # decrypted_message = handleRSAKey(conn)

    while True:
        username = riceviMsg(conn)
       # save_aes_key(username, decrypted_message)
        if username not in utenti:
            break
        inviaMsg(conn,{"testo":"Username occupato scegline un altro"})

    print((f"aggiunto utente: {username}"))
    
    utenti[username] = [conn]

    while True:

        msg=riceviMsg(conn)
        
        print("Messaggio ricevuto:", msg)

        tipoMsg = msg["tipo"]

        match tipoMsg:
            case "messaggio": messaggio(msg),
            case "creaGruppo": creaGruppo(msg),
            case "iniziaConv":iniziaConversazione(msg),
            case "caricaChat": caricaChat(conn,msg)


def main():
    #generationRSAkeys()
    print("Server attivo e in ascolto...")

    while True:
        conn, addr = sServer.accept()
        threading.Thread(target=gestisciClient, args=(conn,)).start()


if __name__ == "__main__":
    main()
