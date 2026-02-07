from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.number import bytes_to_long,long_to_bytes
from Crypto.Protocol.KDF import PBKDF2
import Key

def recv_exact(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            raise ConnectionError("Connessione chiusa")
        data += packet
    return data

def crea_aes_key(file_path="aes.key"):
    salt_pwd = get_random_bytes(16)
    salt_key = get_random_bytes(16)
    nonce = get_random_bytes(12)
    key_to_save = get_random_bytes(32)

    password = input("Inserisci password per la creazione della chiave: ").encode()

    pwd_hash = PBKDF2(password, salt_pwd, dkLen=32, count=200000)

    key_master = PBKDF2(password, salt_key, dkLen=32, count=200000)
    cipher = AES.new(key_master, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(key_to_save)

    with open(file_path, "wb") as f:
        f.write(salt_pwd)
        f.write(pwd_hash)
        f.write(salt_key)
        f.write(nonce)
        f.write(ciphertext)
        f.write(tag)
    return Key.Key(key=key_to_save, nonce=nonce)

def carica_aes_key(file_path="aes.key"): 
    with open(file_path, "rb") as f:
        salt_pwd = f.read(16)
        stored_hash = f.read(32)
        salt_key = f.read(16)
        nonce = f.read(12)
        ciphertext = f.read(32)
        tag = f.read(16)

    for i in range(3):
        password = input("Password: ").encode()
        pwd_hash = PBKDF2(password, salt_pwd, dkLen=32, count=200000)

        if pwd_hash != stored_hash:
            print("Password errata")
            if i == 2:
                raise ValueError("Troppi tentativi")
        else:
            break

    key_master = PBKDF2(password, salt_key, dkLen=32, count=200000)
    cipher = AES.new(key_master, AES.MODE_GCM, nonce=nonce)
    key = cipher.decrypt_and_verify(ciphertext, tag)

    return Key.Key(key=key, nonce=nonce)

def get_aes_key(): 
    import os
    if not os.path.exists('aes.key'):
        return crea_aes_key()
    else:
        return carica_aes_key('aes.key')

def ricevere_RSAkey(socket):    
    pub = socket.recv(4096)
    pub = RSA.import_key(pub)
    print("rcv")
    return pub

def cripta_RSA(pub, aes_key):  
    n=pub.n
    e=pub.e
    encrypted=pow(bytes_to_long(aes_key.key),e,n)
    print("encr")
    return long_to_bytes(encrypted)

def sendAESkey(encrypted_key, socket): 
    print("send")
    socket.sendall(encrypted_key)
#TEST MAIN: Funziona
#    
#    def main():
#        key = get_aes_key()
#    
#        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        client.connect(('localhost', 5000))
#    
#        print("connesso al server!")
#    
#        user = input("inserire nome utente: ")
#        client.sendall(user.encode())
#    
#        public_key = ricevere_RSAkey(client)
#        encripted_key = cripta_RSA(public_key, key)
#        client.sendall(len(encripted_key).to_bytes(4, 'big'))
#        sendAESkey(encripted_key, client)
#    
#        testo = input("inserire messaggio da inviare: ")
#        encrypted_text, tag, nonce = key.criptare(testo)
#        print("testo criptato:", encrypted_text.hex())
#        client.sendall(tag)
#        print("tag inviato:", len(tag))
#        client.sendall(nonce)
#        print("nonce inviato:", len(nonce))
#        client.sendall(len(encrypted_text).to_bytes(4, 'big'))
#        client.sendall(encrypted_text)
#        print("testo inviato:", len(encrypted_text))
#    
#        tag = recv_exact(client, 16)
#        nonce = recv_exact(client, 12)
#        msg_len = int.from_bytes(recv_exact(client, 4), 'big')
#        encrypted_msg = recv_exact(client, msg_len)  # Assicurati di leggere l'intera risposta cifrata
#        decrypted_response = key.decriptare(encrypted_msg, tag, nonce)
#        print("Risposta dal server:", decrypted_response.decode() if isinstance(decrypted_response, bytes) else decrypted_response)
#    
#        client.close()
#    
#    if __name__ == "__main__":
#        main()
