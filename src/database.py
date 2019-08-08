import redis
import base64
import textwrap
import json

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


def push_file(name, file):
    print('Pushing file...')
    b64 = str(file_to_base64(file))
    blocks = textwrap.wrap(b64, BLOCK_SIZE)

    for block in blocks:
        push_block(block, get_available_nodes())


def get_available_nodes():
    return []


def push_block(block, nodes):
    for node in nodes:
        print('pushing block' + block + 'to node' + node)


def handle_response(res):
    data = json.loads(res)
    blocks = data['blocks']
    for block_id, block_hash in blocks.items():
        print('Block ID: ' + block_id + ' Hash: ' + block_hash)
