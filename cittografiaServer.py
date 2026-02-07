from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long,long_to_bytes
import Key

def recv_exact(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            raise ConnectionError("Connessione chiusa")
        data += packet
    return data

def get_private_key(password="ciaoSonoUnaPassword"):    #TESTATO: funziona
    private_key_data = open("generate_RSA_keys/private_key.pem", "rb").read()
    return RSA.import_key(private_key_data, passphrase=password)

def get_public_key():   #TESTATO: funziona
    public_key_data = open("generate_RSA_keys/public_key.pem", "rb").read()
    return RSA.import_key(public_key_data)

def genera_RSAkeys():   #TESTATO: funziona
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
    msg_len = int.from_bytes(recv_exact(conn, 4), 'big')
    AES_key = recv_exact(conn, msg_len)
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
    print("chiave appena decifrata: ", len(key_bytes))
    key = Key.Key(key=key_bytes)
    return key

#    def main():
#        session = SessionKeyStore()
#        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        server.bind(('localhost', 5000))
#        server.listen(1)
#        print("Server in ascolto su localhost:5000")
#        genera_RSAkeys()
#        while True:
#            conn, addr = server.accept()
#            print(f"Connessione da {addr}")
#            user = conn.recv(1024).decode()
#            sendPublicKeyToClient(conn)
#            encrypted_key = receiveEncryptedAESFromClient(conn)
#            key = decryptMessageRSA(encrypted_key)
#            print("chiave: ", len(key.key))
#            session.create_session(conn, user, key)
#            print("Sessione creata per utente:", user)
        # Qui puoi gestire la ricezione e decifratura dei messaggi
        # Esempio: ricevi un messaggio cifrato dal client
#            tag = recv_exact(conn, 16)
#            nonce = recv_exact(conn,12)
#            msg_len = int.from_bytes(recv_exact(conn, 4), 'big')
#            encrypted_msg = recv_exact(conn, msg_len)  # Assicurati di leggere l'intero messaggio cifrato
#            risposta = key.decriptare(encrypted_msg, tag, nonce)
#            print(f"Messaggio ricevuto da {user}: {risposta}")
        # Rispondi al client (esempio: echo)
#            response = f"Ciao {user}, ho ricevuto il tuo messaggio!"
#            encrypted_response, tag_response, nonce_response = key.criptare(response)
#            conn.sendall(tag_response)
#            conn.sendall(nonce_response)
#            conn.sendall(encrypted_response)
#            conn.close()
#    
#    if __name__ == "__main__":
#        main()
