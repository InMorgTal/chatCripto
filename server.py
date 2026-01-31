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

########## crittografia RSA e AES ############
def decifrare(key, encrypted_message, iv, pad_count):
    decrypt = AES.new(key, AES.MODE_CBC, iv)
    text = decrypt.decrypt(encrypted_message)
    if pad_count > 0:
        return text[:-pad_count].decode()
    return text.decode()

def generationRSAkeys():

    key = RSA.generate(2048)

    private_key = key.export_key(passphrase="ciaoSonoUnaPassword")
    with open("generate_RSA_keys/private_key.pem", "wb") as f:
        f.write(private_key)

    public_key = key.publickey().export_key()
    with open("generate_RSA_keys/public_key.pem", "wb") as f:
        f.write(public_key)

def sendPublicKeyToClient(conn):

    with open("generate_RSA_keys/public_key.pem", "rb") as f:
        public_key_data = f.read()
    
    conn.sendall(public_key_data)

def receiveEncryptedAESFromClient(conn):       
    AES_key = conn.recv(4096)  # Dimensione buffer adeguata al messaggio cifrato
    return AES_key

def save_aes_key(nome, key, conn):
    global utenti
    utenti[conn] = [nome, key]

def decryptMessageRSA(AES_key_encrypted, conn):

    private_key_data = open("generate_RSA_keys/private_key.pem", "rb").read()
    pvt = RSA.import_key(private_key_data, passphrase="ciaoSonoUnaPassword")

    n = pvt.n
    d = pvt.d

    encrypted_int = int.from_bytes(AES_key_encrypted, byteorder='big')
    decrypted_int = pow(encrypted_int, d, n)
    
    # Calcola la lunghezza in byte della chiave privata
    key_length_bytes = (pvt.size_in_bits() + 7) // 8
    AES_key = decrypted_int.to_bytes(key_length_bytes, byteorder='big').lstrip(b'\x00')

    save_aes_key(utenti[conn][0], AES_key, conn)

    return AES_key

def handleRSAKey(conn):
    sendPublicKeyToClient(conn)
    encrypted_message = receiveEncryptedAESFromClient(conn)
    decrypted_message = decryptMessageRSA(encrypted_message, conn)
    return decrypted_message

def decifrare(key, encrypted_message, iv, pad_count):
    decrypt = AES.new(key, AES.MODE_CBC, iv)
    text = decrypt.decrypt(encrypted_message)
    if pad_count > 0:
        return text[:-pad_count].decode()
    return text.decode()

def encrypt(text,cipher):
    cont_pad=0
    while len(text.encode())%16!=0:#In modalità CBC il messaggio deve avere un multiplo di 16 bytes
        text+="0"
        cont_pad+=1
    return cont_pad,cipher.encrypt(text.encode())

def cifrare(key, text):
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    pad_count,cifrato= encrypt(text,cipher)
    return iv + pad_count.to_bytes(1, byteorder='big') + cifrato

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
            iv = pacchetto["iv"]
            cPad = pacchetto["cPad"]
            msgCifrato = pacchetto["msgCifrato"]

            # Decifra la parte cifrata (devi avere la funzione decifra)
            msg_decriptato_bytes = decifrare(utenti[conn][1], iv, cPad, msgCifrato)
            msg_decriptato_str = msg_decriptato_bytes.decode()  # da bytes a stringa
            msg = json.loads(msg_decriptato_str)  # messaggio originale JSON

    match msg["tipo"]:
        case "caricaChat":
            for nomechat in msg["chat"]:
                print(nomechat)

def inviaMsg(conn,msg):
    global utenti
    msg=(json.dumps(msg)+ "\n").encode()
    iv, cPad, msgCifrato = cifrare(utenti[conn][1], msg)

# Mettiamo tutto in un dizionario
    pacchetto = {
        "iv": iv,
        "cPad": cPad,
        "msgCifrato": msgCifrato
}

    dati_da_inviare = json.dumps(pacchetto) + "\n"
    conn.sendall(dati_da_inviare.encode())
##############################################

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

    while True:
        username = riceviMsg(conn)["username"]
        
        if username not in utenti:
            break
        inviaMsg(conn,{"testo":"Username occupato scegline un altro"})

    print((f"aggiunto utente: {username}"))
    
    utenti[username] = conn

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

    print("Server attivo e in ascolto...")

    while True:
        conn, addr = sServer.accept()

        threading.Thread(target=gestisciClient, args=(conn,)).start()


if __name__ == "__main__":
    main()
