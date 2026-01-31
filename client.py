# Importa le librerie necessarie per la comunicazione via socket e il multithreading
import socket
import threading
import os
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

############################################
#creare chiave AES e salvarla
def create_aes_key(file_path):
    key = get_random_bytes(16)  # AES-128
    with open(file_path, 'wb') as key_file:
        key_file.write(key)
    return key

def receiveRSAkey(socket):
    pub = socket.recv(1024)
    return pub

def encrypt_RSA(pub, AES_key):
    n=pub.n
    e=pub.e
    encrypted=pow(AES_key,e,n)
    return encrypted
#non evocare
def sendAESkey(key, socket):
    socket.sendall(key)

def first_time_setup(socket):
    key_file = 'aes_key.bin'
    try:
        key = load_aes_key(key_file)
    except FileNotFoundError:
        key = create_aes_key(key_file)

    public_key = receiveRSAkey(socket)
    encrypted_AES = encrypt_RSA(public_key, key)
    sendAESkey(encrypted_AES, socket)

def encrypt(text,cipher):
    cont_pad=0
    while len(text.encode())%16!=0:#In modalità CBC il messaggio deve avere un multiplo di 16 bytes
        text+="0"
        cont_pad+=1
    return cont_pad,cipher.encrypt(text.encode())
##############################################
#cifrare messaggio
def cifrare(key, text):
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    pad_count,cifrato= encrypt(text,cipher)
    return iv, pad_count.to_bytes(1, byteorder='big'), cifrato    #Mandare ogni parametro al server
#decifrare messaggio
def decifrare(key, encrypted_message, iv, pad_count):
    decrypt = AES.new(key, AES.MODE_CBC, iv)
    text = decrypt.decrypt(encrypted_message)
    if pad_count > 0:
        return text[:-pad_count].decode()
    return text.decode()
#caricare chiave AES da file
def load_aes_key(file_path):
    with open(file_path, 'rb') as key_file:
        key = key_file.read()
    return key

#globali
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
            pacchetto = json.loads(msg_str)  # pacchetto con iv, cPad, msgCifrato

            # Decifriamo il messaggio
            iv = pacchetto["iv"]
            cPad = pacchetto["cPad"]
            msgCifrato = pacchetto["msgCifrato"]

            # Decifra la parte cifrata (devi avere la funzione decifra)
            msg_decriptato_bytes = decifrare(load_aes_key('aes_key.bin'), iv, cPad, msgCifrato)
            msg_decriptato_str = msg_decriptato_bytes.decode()  # da bytes a stringa
            msg = json.loads(msg_decriptato_str)  # messaggio originale JSON

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
    msg=(json.dumps(msg)+ "\n").encode()
    iv, cPad, msgCifrato = cifrare(load_aes_key('aes_key.bin'), msg)

# Mettiamo tutto in un dizionario
    pacchetto = {
        "iv": iv,
        "cPad": cPad,
        "msgCifrato": msgCifrato
}

    dati_da_inviare = json.dumps(pacchetto) + "\n"
    conn.sendall(dati_da_inviare.encode())

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
