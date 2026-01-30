'''Implementare una chat client server con Thread che sia in grado di gestire lo scambio di messaggi sia in Broadcast che Unicast.
l'utente("Client") deve poter scrivere il proprio Username in un dizionario gestito dal server ed essere quindi in grado sia di inviare messaggi a singoli client
(inserendo l'user destinatario con la seguente dicitura @user ) che in broadcast.
'''

import socket
import threading
from Crypto.PublicKey import RSA


sServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sServer.bind(('localhost', 5000))

sServer.listen()

utenti = {}

def gestisci_client(conn, addr):
    """
    Gestisce la comunicazione con un singolo client.
    - Riceve l'username del client
    - Verifica che non sia già occupato
    - Riceve e elabora i messaggi (broadcast o privati)
    """

    while True:
        username = conn.recv(1024).decode().strip()
        
        if username not in utenti:

            break
        conn.sendall("Username occupato scegline un altro\n".encode())

    print((f"aggiunto utente: {username}"))
    
    utenti[username] = conn

    while True:
        try:

            msg = conn.recv(1024).decode().strip()
            
            if not msg:
                break












def generationRSAkeys():
    """
    Genera una coppia di chiavi RSA a 2048 bit e le salva su disco.
    Comportamento:
    - Genera una chiave RSA a 2048 bit.
    - Esporta la chiave privata in formato PKCS#8 cifrata con la passphrase "ciaoSonoUnaPassword"
        e la protezione "scryptAndAES128-CBC", salvandola in 'generate_RSA_keys/private_key.pem'.
    - Esporta la chiave pubblica e la salva in 'generate_RSA_keys/public_key.pem'.
    Parametri:
    - Nessuno.
    Valore di ritorno:
    - None.
    Eccezioni:
    - Potrebbe sollevare errori di I/O se la scrittura su file fallisce o eccezioni dalla libreria crittografica
        in caso di problemi nella generazione/esportazione delle chiavi.
    Avvertenze:
    - La passphrase è hardcoded: per la produzione usare una gestione sicura delle credenziali.
    - Verificare l'esistenza e i permessi della directory 'generate_RSA_keys' prima dell'esecuzione.
    """
    key = RSA.generate(2048)

    private_key = key.export_key(passphrase="ciaoSonoUnaPassword", pkcs=8,
                                 protection="scryptAndAES128-CBC")
    with open("generate_RSA_keys/private_key.pem", "wb") as f:
        f.write(private_key)

    public_key = key.publickey().export_key()
    with open("generate_RSA_keys/public_key.pem", "wb") as f:
        f.write(public_key)

def sendPublicKeyToClient(conn):

    """
    Invia la chiave pubblica RSA al client connesso.
    Parametri:
    - conn: socket del client a cui inviare la chiave pubblica.
    Valore di ritorno:
    - None.
    Eccezioni:
    - Potrebbe sollevare errori di I/O se la lettura del file fallisce o eccezioni di socket
        in caso di problemi durante l'invio della chiave.
    Avvertenze:
    - Assicurarsi che il file 'generate_RSA_keys/public_key.pem' esista e sia accessibile.
    """
    with open("generate_RSA_keys/public_key.pem", "rb") as f:
        public_key_data = f.read()
    
    conn.sendall(public_key_data)

def receiveEncryptedAESFromClient(conn):
    """
    Riceve un messaggio cifrato RSA dal client.
    Parametri:
    - conn: socket del client da cui ricevere il messaggio cifrato.
    Valore di ritorno:
    - Il messaggio cifrato ricevuto (in bytes).
    Eccezioni:
    - Potrebbe sollevare eccezioni di socket in caso di problemi durante la ricezione del messaggio.
    Avvertenze:
    - Assicurarsi che il client invii correttamente il messaggio cifrato.
    """
    AES_key = conn.recv(4096)  # Dimensione buffer adeguata al messaggio cifrato
    return AES_key

def decryptMessageRSA(encrypted_message):
    """
    Decripta un messaggio cifrato RSA usando la chiave privata.
    Parametri:
    - encrypted_message: il messaggio cifrato da decriptare (in bytes).
    Valore di ritorno:
    - Il messaggio decriptato (in bytes).
    Eccezioni:
    - Potrebbe sollevare errori di I/O se la lettura del file fallisce o eccezioni dalla libreria crittografica
        in caso di problemi durante la decriptazione.
    Avvertenze:
    - Assicurarsi che il file 'generate_RSA_keys/private_key.pem' esista e sia accessibile.
    """
    private_key_data = open("generate_RSA_keys/private_key.pem", "rb").read()
    pvt = RSA.import_key(private_key_data, passphrase="ciaoSonoUnaPassword")

    n = pvt.n
    d = pvt.d

    encrypted_int = int.from_bytes(encrypted_message, byteorder='big')
    decrypted_int = pow(encrypted_int, d, n)
    
    # Calcola la lunghezza in byte della chiave privata
    key_length_bytes = (pvt.size_in_bits() + 7) // 8
    AES_key = decrypted_int.to_bytes(key_length_bytes, byteorder='big').lstrip(b'\x00')

    return AES_key

def handleRSAKey(conn):
    """
    Gestisce lo scambio di chiavi RSA e la decriptazione del messaggio.
    Parametri:
    - conn: socket del client connesso.
    Valore di ritorno:
    - Il messaggio decriptato (in bytes).
    Eccezioni:
    - Potrebbe sollevare errori di I/O o eccezioni di socket in caso di problemi durante lo scambio di chiavi
        o la decriptazione.
    Avvertenze:
    - Assicurarsi che i file delle chiavi esistano e siano accessibili.
    """
    sendPublicKeyToClient(conn)
    encrypted_message = receiveEncryptedAESFromClient(conn)
    decrypted_message = decryptMessageRSA(encrypted_message)
    return decrypted_message

#MANCA GESTIONE PER ONGI CLIENT
#mANCA LOGICA PER INVIARE IL MESSAGGIO SOLO AL CLIENT MITTENTE

def receiiveEncryptedMessageFromClient(conn):
    """
    Riceve un messaggio cifrato AES dal client.
    Parametri:
    - conn: socket del client da cui ricevere il messaggio cifrato.
    Valore di ritorno:
    - Il messaggio cifrato ricevuto (in bytes).
    Eccezioni:
    - Potrebbe sollevare eccezioni di socket in caso di problemi durante la ricezione del messaggio.
    Avvertenze:
    - Assicurarsi che il client invii correttamente il messaggio cifrato.
    """
    encrypted_message = conn.recv(4096)  # Dimensione buffer adeguata al messaggio cifrato
    return encrypted_message

def decryptMessageAES(encrypted_message, AES_key):
    """
    Decripta un messaggio cifrato AES usando la chiave AES fornita.
    Parametri:
    - encrypted_message: il messaggio cifrato da decriptare (in bytes).
    - AES_key: la chiave AES da utilizzare per la decriptazione (in bytes).
    Valore di ritorno:
    - Il messaggio decriptato (in bytes).
    Eccezioni:
    - Potrebbe sollevare eccezioni dalla libreria crittografica in caso di problemi durante la decriptazione.
    """
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad

    cipher = AES.new(AES_key, AES.MODE_CBC, iv=encrypted_message[:16])
    decrypted_message = unpad(cipher.decrypt(encrypted_message[16:]), AES.block_size)
    return decrypted_message

def encryptMessageAES(message, AES_key):
    """
    Cifra un messaggio usando la chiave AES fornita.
    Parametri:
    - message: il messaggio da cifrare (in bytes).
    - AES_key: la chiave AES da utilizzare per la cifratura (in bytes).
    Valore di ritorno:
    - Il messaggio cifrato (in bytes).
    Eccezioni:
    - Potrebbe sollevare eccezioni dalla libreria crittografica in caso di problemi durante la cifratura.
    """
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    from Crypto.Random import get_random_bytes

    iv = get_random_bytes(16)
    cipher = AES.new(AES_key, AES.MODE_CBC, iv)
    encrypted_message = iv + cipher.encrypt(pad(message, AES.block_size))
    return encrypted_message

def handleAESMessage(conn, AES_key):
    """
    Gestisce la ricezione e decriptazione di un messaggio AES.
    Parametri:
    - conn: socket del client connesso.
    - AES_key: la chiave AES da utilizzare per la decriptazione (in bytes).
    """
    encrypted_message = receiiveEncryptedMessageFromClient(conn)
    decrypted_message = decryptMessageAES(encrypted_message, AES_key)
    return decrypted_message

def sendEncryptedMessageToClient(conn, message, AES_key):
    """
    Cifra e invia un messaggio AES al client.
    Parametri:
    - conn: socket del client a cui inviare il messaggio cifrato.
    - message: il messaggio da cifrare e inviare (in bytes).
    - AES_key: la chiave AES da utilizzare per la cifratura (in bytes).
    """
    encrypted_message = encryptMessageAES(message, AES_key)
    conn.sendall(encrypted_message)




def main():
    """
    Avvia il server e rimane in ascolto per accettare connessioni dai client.
    Per ogni client che si connette, crea un thread separato che lo gestisce.
    """

    print("Server attivo e in ascolto...")

    while True:
        conn, addr = sServer.accept()

        print(f"[+] Connessione da {addr}")

        threading.Thread(target=gestisci_client, args=(conn, addr)).start()


# Punto di ingresso del programma
if __name__ == "__main__":
    main()
