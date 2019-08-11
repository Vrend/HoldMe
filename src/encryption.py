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
    pre_data = nonce + b'data:' + ciphertext + b'tag:' + tag
    data = base64.b64encode(pre_data)
    return data


def decrypt(password, data):
    data_decoded = base64.b64decode(data)
    split_one = data_decoded.split(b'data:')
    nonce = split_one[0]
    split_two = split_one[1].split(b'tag:')
    ciphertext = split_two[0]
    tag = split_two[1]
    key = PBKDF2(password, salt)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    plaintext = cipher.decrypt(ciphertext)
    try:
        cipher.verify(tag)
        return plaintext
    except ValueError:
        return 'Bad Password'
