from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.number import bytes_to_long,long_to_bytes
#Client
############################################
#creare chiave AES e salvarla
def create_aes_key(file_path):
    global my_iv
    key = get_random_bytes(16)  # AES-128
    cipher=AES.new(key,mode=AES.MODE_CBC)
    my_iv = cipher.iv
    with open(file_path, 'wb') as key_file:
        key_file.write(bytes_to_long(cipher))
    return key

def receiveRSAkey(socket):
    pub = socket.recv(1024).decode()
    pub=RSA.import_key(pub)
    print("rcv")
    return pub

def encrypt_RSA(pub, AES_key):
    n=pub.n
    e=pub.e
    encrypted=pow(bytes_to_long(AES_key),e,n)
    print("encr")
    return encrypted
#non evocare
def sendAESkey(key, socket):
    print("send")
    socket.sendall(long_to_bytes(key))

def mandare_AES_key(socket):
    key_file = 'aes_key.bin'
    try:
        print("loadAES")
        key, iv = load_aes_key(key_file)
    except FileNotFoundError:
        print("createAES")
        key, iv = create_aes_key(key_file)

    print("inizio rcv pub key")
    public_key = receiveRSAkey(socket)
    print("encrypt aes ")
    encrypted_AES = encrypt_RSA(public_key, key)
    print("manda aes criptata")
    sendAESkey(encrypted_AES, socket)

def encrypt(text,cipher):
    cont_pad=0
    while len(text)%16!=0:#In modalità CBC il messaggio deve avere un multiplo di 16 bytes
        text+="0"
        cont_pad+=1
    return cont_pad,cipher.encrypt(text.encode())
##############################################
#cifrare messaggio
def cifrare(key, text):
    global my_iv
    iv = my_iv
    cipher = load_aes_key()
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
#fine parte client
#Server
########## crittografia RSA e AES ############
def decifrare(key, encrypted_message, iv, pad_count):
    decrypt = AES.new(key, AES.MODE_CBC, iv)
    text = decrypt.decrypt(encrypted_message)
    if pad_count > 0:
        return text[:-pad_count].decode()
    return text.decode()

def generationRSAkeys():
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
    with open("generate_RSA_keys/public_key.pem", "rb") as f:
        public_key_data = f.read()
    
    conn.sendall(public_key_data)
    print("fine chiave pubblica")

def receiveEncryptedAESFromClient(conn):   
    print("riceve chiave aes")    
    AES_key = conn.recv(4096)  # Dimensione buffer adeguata al messaggio cifrato
    print("fine chiave aes")  
    return AES_key

def save_aes_key(nome, key):
    global utenti
    utenti[nome].append(key)

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
#fine parte server
def load_aes_key(file_path):
    with open(file_path, 'rb') as key_file:
        key = long_to_bytes(key_file.read())
    return key

