import base64
import hashlib
from Cryptodome.Cipher import AES
import configparser

config = configparser.ConfigParser()
config.read_file(open('config/config.ini'))
SECRET_KEY = config['database']['encryption_key']

BS = 16
pad = (lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS).encode())
unpad = (lambda s: s[:-ord(s[len(s)-1:])])

class AESCipher(object):
    def __init__(self):
        self.key = hashlib.sha256(SECRET_KEY.encode()).digest()
    
    def encrypt(self, message):
        message = message.encode()
        raw = pad(message)
        cipher = AES.new(self.key, AES.MODE_CBC, self.__iv().encode('utf8'))
        enc = cipher.encrypt(raw)
        return base64.b64encode(enc).decode('utf-8')
    
    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_CBC, self.__iv().encode('utf8'))
        dec = cipher.decrypt(enc)
        return unpad(dec).decode('utf-8')
    
    def __iv(self):
        return chr(0) * 16
