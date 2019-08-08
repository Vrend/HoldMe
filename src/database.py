import redis
import base64
import textwrap
from encryption import *

BLOCK_SIZE = 512

OPTIMAL_NODES = 20

MINIMUM_NODES = 10


def test_redis():
    r = redis.Redis()
    return str(r.ping())


def file_to_base64(file):
    return base64.b64encode(file.read())


def base64_to_file(string):
    return base64.b64decode(string)


def push_file(name, password, file):
    print('Pushing file...')
    data = encrypt(password, file_to_base64(file))
    blocks = textwrap.wrap(data.decode(), BLOCK_SIZE)

    for block in blocks:
        print(block)
        push_block(block, get_available_nodes())


def rebuild_file(password, blocks):
    master = ''
    for block in blocks:
        master.join(block)
    plaintext = decrypt(password, master.encode())
    return base64_to_file(plaintext)


def test_encryption_decryption():
    plaintext = 'dank memes my dude'.encode()
    password = 'ya hate to see it!@$'
    data = encrypt(password, plaintext)
    return decrypt(password, data)


def get_available_nodes():
    return []


def push_block(block, nodes):
    for node in nodes:
        print('pushing block' + block + 'to node' + node)


def handle_response(res):
    blocks = res['blocks']
    for block_id, block_hash in blocks.items():
        print('Block ID: ' + block_id + ' Hash: ' + block_hash)
