from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
class Key:
    def __init__(self, key, nonce=None):
        self.key = key
        if nonce is None:
            from Crypto.Random import get_random_bytes
            self.nonce = get_random_bytes(12)  # 12 bytes standard per AES-GCM
        else:
            self.nonce = nonce
    def criptare(self, testo):
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=self.nonce)
        if isinstance(testo, str):
            testo = testo.encode()
        encrypted_text, tag = cipher.encrypt_and_digest(testo)
        nonce = self.nonce
        self.nonce = get_random_bytes(12)  # Aggiorna il nonce per la prossima operazione
        return encrypted_text, tag, nonce
        
    def decriptare(self, encrypted_text, tag, nonce):
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        decrypted_text = cipher.decrypt_and_verify(encrypted_text, tag)
        try:
            return decrypted_text.decode()
        except UnicodeDecodeError:
            return decrypted_text
    def to_bytes(self):
        # Serializza salt, nonce, tag, key
        return self.nonce + self.key
    @staticmethod
    def from_bytes(data):
        # salt(16) + nonce(12) + tag(16) + key(32)
        nonce = data[:12]
        key = data[12:44]
        return Key(key=key, nonce=nonce)
    def __str__(self):
        return f"Key(key={self.key.hex()}, tag={self.tag.hex()}, salt={self.salt.hex()}, nonce={self.nonce.hex()}, password={'***' if self.password else ''})"
