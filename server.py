'''Implementare una chat client server con Thread che sia in grado di gestire lo scambio di messaggi sia in Broadcast che Unicast.
l'utente("Client") deve poter scrivere il proprio Username in un dizionario gestito dal server ed essere quindi in grado sia di inviare messaggi a singoli client
(inserendo l'user destinatario con la seguente dicitura @user ) che in broadcast.
'''

# Importa le librerie necessarie per la comunicazione via socket e il multithreading
import socket
import threading
from Crypto.PublicKey import RSA

# Crea un socket server TCP/IP per accettare connessioni dai client
sServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Lega il server all'indirizzo localhost e alla porta 5000
sServer.bind(('localhost', 5000))

# Mette il server in ascolto per accettare connessioni in arrivo
sServer.listen()

# Dizionario che memorizza gli utenti connessi: {username: socket_del_client}
# Viene usato per le comunicazioni broadcast e unicast
utenti = {}


# Funzione che gestisce ogni client connesso al server
# Viene eseguita in un thread separato per ogni client
def gestisci_client(conn, addr):
    """
    Gestisce la comunicazione con un singolo client.
    - Riceve l'username del client
    - Verifica che non sia già occupato
    - Riceve e elabora i messaggi (broadcast o privati)
    """

    # Loop per richiedere l'username finché non è disponibile
    while True:
        # Riceve l'username dal client (massimo 1024 byte) e lo decodifica
        username = conn.recv(1024).decode().strip()
        
        # Controlla se l'username è già stato registrato
        if username not in utenti:
            # Se non esiste, esce dal loop e registra l'utente
            break
        
        # Se l'username è già occupato, invia un messaggio d'errore al client
        conn.sendall("Username occupato scegline un altro\n".encode())

    # Stampa un messaggio di conferma nel log del server
    print((f"aggiunto utente: {username}"))
    
    # Associa l'username del client alla sua socket nel dizionario
    # Questo permette di inviare messaggi privati e broadcast a questo client
    utenti[username] = conn

    # Loop principale: gestisce tutti i messaggi inviati dal client
    while True:
        try:
            # Riceve il messaggio dal client, lo decodifica e rimuove spazi/newline
            msg = conn.recv(1024).decode().strip()
            
            # Se il messaggio è vuoto, il client si è disconnesso
            if not msg:
                break

            # Controlla se il messaggio è privato (inizia con @)
            if msg.startswith("@"):
                try:
                    # Divide il messaggio in massimo 2 parti: ["@destinatario", "testo del messaggio"]
                    parti = msg.split(" ", 1)

                    # Controlla che il formato sia corretto (@ e messaggio)
                    if len(parti) < 2:
                        conn.sendall("Formato non valido. Usa: @destinatario messaggio\n".encode())
                        continue

                    # Estrae il nome del destinatario rimuovendo il simbolo @
                    dest = parti[0][1:]

                    # Estrae il testo del messaggio (la seconda parte)
                    msg = parti[1]

                    # Verifica che il destinatario esista e non sia se stesso
                    if dest in utenti and dest != username:
                        # Invia il messaggio privato al destinatario
                        utenti[dest].sendall(f"[{username} (in privato) ]: {msg}".encode())
                    else:
                        # Se il destinatario non esiste, invia un messaggio d'errore
                        conn.sendall(f"Impossibile inviare il messaggio\n".encode())

                except ValueError:
                    # Se c'è un errore nel parsing, segnala il formato non valido
                    conn.sendall("Formato non valido. Usa: @destinatario messaggio\n".encode())

            else:
                # Messaggio broadcast: invia a tutti gli altri client
                # Itera attraverso tutte le socket dei client connessi
                for c in utenti.values():
                    # Invia il messaggio solo agli altri client, non al mittente
                    if c != conn:
                        c.sendall(f"[{username}]:  {msg}".encode())

        except:
            # Se c'è un errore durante la ricezione del messaggio, esce dal loop
            break

    # Fase di disconnessione: pulizia quando il client si disconnette
    print(f"[-] {username} disconnesso")
    
    # Rimuove l'utente dal dizionario dei client connessi
    del utenti[username]
    
    # Chiude la socket del client
    conn.close()

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

# Funzione principale che avvia il server e accetta connessioni
def main():
    """
    Avvia il server e rimane in ascolto per accettare connessioni dai client.
    Per ogni client che si connette, crea un thread separato che lo gestisce.
    """

    # Stampa un messaggio di avvio del server
    print("Server attivo e in ascolto...")

    # Loop infinito: accetta continuamente nuove connessioni dai client
    while True:
        # Accetta una nuova connessione dal client
        # conn = socket del client connesso
        # addr = indirizzo IP e porta del client
        conn, addr = sServer.accept()
        
        # Stampa un messaggio di conferma con l'indirizzo del client connesso
        print(f"[+] Connessione da {addr}")
        
        # Crea un nuovo thread per gestire questo client
        # target = funzione da eseguire nel thread (gestisci_client)
        # args = argomenti da passare alla funzione (conn e addr)
        # .start() = avvia il thread
        threading.Thread(target=gestisci_client, args=(conn, addr)).start()


# Punto di ingresso del programma
if __name__ == "__main__":
    main()
