from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.number import bytes_to_long,long_to_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
import socket
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
