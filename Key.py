from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.number import bytes_to_long,long_to_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
import socket
class Key:
    def __init__(self, key, nonce = None):
        self.key = key
        self.nonce = nonce
        if(self.nonce = None)
            self.nonce = get_random_bytes(16)
    def criptare(self, testo):
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=self.nonce)
        encrypted_text, tag = cipher.encrypt_and_digest(testo.encode())
        nonce = self.nonce
        self.nonce = get_random_bytes(16)
        return encrypted_text, tag, nonce
    def decriptare(self, encrypted_text, tag, nonce):
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=self.nonce)
        decrypted_text = cipher.decrypt_and_verify(encrypted_text, tag)
        return decrypted_text.decode()
    def to_string(self):
        return f"{self.key.hex()}, {self.nonce.hex()}"
    def to_bytes(self):
        return self.key + self.nonce
    def __str__(self):
        return f"Key(id={self.id}, key={self.key}, tag={self.tag}, salt={self.salt}, password={self.password})"
