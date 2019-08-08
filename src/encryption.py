import os
import base64
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

salt = os.urandom(16)


def encrypt(password, string):
    key = PBKDF2(password, salt)
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(string)
    pre_data = nonce + b':' + ciphertext + b':' + tag
    data = base64.b64encode(pre_data)
    return data


def decrypt(password, data):
    data_decoded = base64.b64decode(data)
    args = data_decoded.split(b':')
    nonce = args[0]
    ciphertext = args[1]
    tag = args[2]
    key = PBKDF2(password, salt)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    plaintext = cipher.decrypt(ciphertext)
    try:
        cipher.verify(tag)
        return plaintext
    except ValueError:
        print("Bad Password")
