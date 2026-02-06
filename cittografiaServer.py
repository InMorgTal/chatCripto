from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Util.number import bytes_to_long,long_to_bytes
from Crypto.Random import get_random_bytes
import socket
import Key


class SessionKeyStore:
    """
    Mantiene chiavi AES solo in RAM, associate a una connessione
    """
    def __init__(self):
        self._sessions = {}  # conn_id -> session data

    def create_session(self, conn_id, username, aes_key: Key.Key):
        self._sessions[conn_id] = {
            "username": username,
            "aes_key": aes_key
        }

    def get_key(self, conn_id):
        session = self._sessions.get(conn_id)
        return session["aes_key"] if session else None

    def destroy_session(self, conn_id):
        session = self._sessions.pop(conn_id, None)
        if session:
            key = session["aes_key"]
            for i in range(len(key)):
                key[i] = 0  # best-effort zeroing

#Server
########## crittografia RSA e AES ############


def get_private_key(password="ciaoSonoUnaPassword"):
    private_key_data = open("generate_RSA_keys/private_key.pem", "rb").read()
    return RSA.import_key(private_key_data, passphrase=password)

def get_public_key():
    public_key_data = open("generate_RSA_keys/public_key.pem", "rb").read()
    return RSA.import_key(public_key_data)

def genera_RSAkeys():
    print("generazioneRsA")
    key = RSA.generate(2048)

    private_key = key.export_key(passphrase="ciaoSonoUnaPassword")
    with open("generate_RSA_keys/private_key.pem", "wb") as f:
        f.write(private_key)

    public_key = key.publickey().export_key()
    with open("generate_RSA_keys/public_key.pem", "wb") as f:
        f.write(public_key)
    print("Fine generazioneRsA")

def sendPublicKeyToClient(conn):
    print("manda chiave pubblica")
    
    conn.sendall(get_public_key().export_key())
    print("fine chiave pubblica")

def receiveEncryptedAESFromClient(conn):   
    print("riceve chiave aes")    
    AES_key = conn.recv(4096)  # Dimensione buffer adeguata al messaggio cifrato
    print("fine chiave aes")  
    return AES_key

def save_aes_key(nome, key):
    global utenti
    utenti[nome].append(key)

def decryptMessageRSA(AES_key_encrypted):

    pvt = get_private_key()

    n = pvt.n
    d = pvt.d

    encrypted_int = bytes_to_long(AES_key_encrypted)
    decrypted_int = pow(encrypted_int, d, n)
    key_bytes = long_to_bytes(decrypted_int)
    # La password va richiesta all'utente o gestita in altro modo
    key = Key.Key.from_bytes(key_bytes)
    return key


#fine parte server


def main():
    session = SessionKeyStore()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 5000))
    server.listen(1)
    print("Server in ascolto su localhost:5000")
    genera_RSAkeys()
    while True:
        conn, addr = server.accept()
        print(f"Connessione da {addr}")
        user = conn.recv(1024).decode()
        sendPublicKeyToClient(conn)
        encrypted_key = receiveEncryptedAESFromClient(conn)
        key = decryptMessageRSA(encrypted_key)
        session.create_session(conn, user, key)
        # Qui puoi gestire la ricezione e decifratura dei messaggi
        # Esempio: ricevi un messaggio cifrato dal client
        tag = conn.recv(16)
        encrypted_msg = conn.recv(4096)
        risposta = key.decriptare(encrypted_msg, tag)
        print(f"Messaggio ricevuto da {user}: {risposta}")
        # Rispondi al client (esempio: echo)
        response = f"Ciao {user}, ho ricevuto il tuo messaggio!"
        encrypted_response, tag_response = key.criptare(response)
        conn.sendall(tag_response)
        conn.sendall(encrypted_response)
        conn.close()

if __name__ == "__main__":
    main()
