from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.number import bytes_to_long,long_to_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
import socket
import Key

global hash_value

def hash(data):
    data = data.encode()
    hasher = SHA256.new()
    hasher.update(data)
    return hasher.hexdigest()

def creazione_aes_key():
    global hash_value
    salt = get_random_bytes(16)
    key_to_save = get_random_bytes(32)
    nonce = get_random_bytes(12)

    password = input("Inserisci la password per proteggere la chiave AES: ")
    hash_val = hash(password)
    key_master = PBKDF2(password, salt, dkLen=32, count=200000)
    cipher = AES.new(key_master, AES.MODE_GCM, nonce=nonce)
    encrypted_key, tag = cipher.encrypt_and_digest(key_to_save)
    key = Key.Key(key=key_to_save, nonce=nonce)
    with open("aes.key", "wb") as f:
        f.write(salt)
        f.write(tag)
        f.write(encrypted_key)
        f.write(hash_val.encode())
    global hash_value
    hash_value = hash_val
    return key

def esporta_aes_key(file_path='aes.key'):
    with open(file_path, 'rb') as f:
        salt = f.read(16)
        tag = f.read(16)
        encrypted_key = f.read(32)
        hash_val = f.read(64).decode() # SHA256 hex digest è 64 caratteri
    global hash_value
    hash_value = hash_val
    for i in range(3):
        password = input("Inserisci la password per decriptare la chiave AES: ")
        if hash(password) != hash_value:
            if i == 2:
                raise ValueError("Password errata!")
            else:
                print("Password errata, riprova.(tentativo {}/{})".format(i+1, 3))
        else:
            break
    key_master = PBKDF2(password, salt, dkLen=32, count=200000)
    cipher = AES.new(key_master, AES.MODE_GCM)
    key_to_save = cipher.decrypt_and_verify(encrypted_key, tag)
    key = Key.Key(key=key_to_save, nonce=cipher.nonce)
    return key

def get_aes_key():
    import os
    if not os.path.exists('aes.key'):
        return creazione_aes_key()
    else:
        return esporta_aes_key('aes.key')

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
    return encrypted

def sendAESkey(encrypted_key, socket):
    print("send")
    socket.sendall(long_to_bytes(encrypted_key))

def main():
    key = get_aes_key()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 5000))

    print("connesso al server!")

    user = input("inserire nome utente: ")
    client.sendall(user.encode())

    public_key = ricevere_RSAkey(client)
    encripted_key = cripta_RSA(public_key, key)
    sendAESkey(encripted_key, client)

    testo = input("inserire messaggio da inviare: ")
    encrypted_text, tag, nonce = key.criptare(testo)
    print("testo criptato:", encrypted_text.hex())
    client.sendall(tag + encrypted_text + nonce)

    tag = client.recv(16)
    encrypted_response = client.recv(4096)
    decrypted_response = key.decriptare(encrypted_response, tag)
    print("Risposta dal server:", decrypted_response.decode() if isinstance(decrypted_response, bytes) else decrypted_response)

    client.close()

if __name__ == "__main__":
    main()
