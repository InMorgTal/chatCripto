from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.number import bytes_to_long,long_to_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
import socket
#Client
############################################
#creare chiave AES e salvarla

global contatore
global hash_value

class Key:
    contatore = 0
    def __init__(self, key, tag, salt, password):
        self.id = Key.contatore
        self.key = key
        self.tag = tag
        self.salt = salt
        self.password = password
        Key.contatore += 1
    def criptare(self, testo):
        master_key = PBKDF2(self.password, self.salt, dkLen=32, count=200000)
        cipher = AES.new(master_key, AES.MODE_GCM, nonce=self.id.to_bytes(16, byteorder='big'))
        encrypted_text, tag = cipher.encrypt_and_digest(testo.encode())
        return encrypted_text, tag
    def decriptare(self, encrypted_text, tag):
        master_key = PBKDF2(self.password, self.salt, dkLen=32, count=200000)
        cipher = AES.new(master_key, AES.MODE_GCM, nonce=self.id.to_bytes(16, byteorder='big'))
        decrypted_text = cipher.decrypt_and_verify(encrypted_text, tag)
        return decrypted_text.decode()
    def to_string(self):
        return f"{self.id},{self.key.hex()},{self.tag.hex()},{self.salt.hex()},{self.password}"
    def to_bytes(self):
        return (f"{self.id},{self.key.hex()},{self.tag.hex()},{self.salt.hex()},{self.password}").encode()
    def __str__(self):
        return f"Key(id={self.id}, key={self.key}, tag={self.tag}, salt={self.salt}, password={self.password})"


def hash(data):
    data = data.encode()
    hasher = SHA256.new()
    hasher.update(data)
    return hasher.hexdigest()

def creazione_aes_key(key):
    global hash_value
    
    password = input("Inserisci la password per proteggere la chiave AES: ")
    hash_value = hash(password)
    key_master = PBKDF2(password, salt, dkLen=32, count=200000)

    salt = get_random_bytes(16)
    key_to_save = get_random_bytes(32)
    cipher = AES.new(key_master, AES.MODE_GCM, key.id)
    encrypted_key, tag = cipher.encrypt_and_digest(key_to_save)

    with open("aes.key", "wb") as f:
        f.write(salt)
        f.write(key.id.to_bytes(16, byteorder='big'))
        f.write(tag)
        f.write(encrypted_key)

#SETUP: creare chiave AES se non esiste MA se esiste fare invece il load

def esporta_aes_key(file_path='aes.key', aes_key=Key()):
    global hash_value
    for i in range(3):
        password = input("Inserisci la password per decriptare la chiave AES: ")
        if hash(password) != hash_value:
            if i == 2:
                raise ValueError("Password errata!")
            else:
                print("Password errata, riprova.(tentativo {}/{})".format(i+1, 3))
        else:
            break
    aes_key.password = password
    with open(file_path, 'rb') as f:
        salt = f.read(16)
        nonce = f.read(16)
        tag = f.read(16)
        encrypted_key = f.read()

    aes_key.id = nonce
    aes_key.salt = salt
    aes_key.tag = tag
    aes_key.key = encrypted_key
    
def ricevere_RSAkey(socket):
    pub = socket.recv(1024).decode()
    pub=RSA.import_key(pub)
    print("rcv")
    return pub

def cripta_RSA(pub, aes_key):
    n=pub.n
    e=pub.e
    encrypted=pow(bytes_to_long(aes_key.to_bytes()),e,n)
    print("encr")
    return encrypted

def sendAESkey(encrypted_key, socket):
    print("send")
    socket.sendall(long_to_bytes(encrypted_key))

def aes_key(key):
    with open('aes_key.bin', 'r') as f:
        if not f.read(1):
            creazione_aes_key(key)
            esporta_aes_key('aes_key.bin', key)
        else:
            esporta_aes_key('aes_key.bin', key)
#fine parte client

def main():
    key = Key()
    aes_key(key)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 5000))

    print("connesso al server!")

    public_key = ricevere_RSAkey(client)
    encripted_key = cripta_RSA(public_key, key)
    sendAESkey(encripted_key, client)

if __name__ == "__main__":
    main()
