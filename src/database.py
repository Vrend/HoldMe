import textwrap
from encryption import *
import uuid
import redis
from passlib.hash import md5_crypt
import pickle
import time

BLOCK_SIZE = 1024

OPTIMAL_NODES = 20

MINIMUM_NODES = 10


def test_redis():
    r = redis.Redis()
    return str(r.ping())


def file_to_base64(file):
    return base64.b64encode(file.read())


def base64_to_file(string):
    return base64.b64decode(string)


def push_file(name, password, file, socketio):
    r = redis.Redis()
    print('Pushing file...')
    plaintext = file_to_base64(file)
    data = encrypt(password, plaintext)
    blocks = textwrap.wrap(data.decode(), BLOCK_SIZE)

    i = 0
    for block in blocks:
        block_id = uuid.uuid1().hex
        # Set block to file name hashtable
        block_hash = md5_crypt.hash(block)
        r.hset('file-'+name, 'block'+str(i), block_id)
        # Set connection between block id and hash
        r.hset(block_id, 'hash', block_hash)
        nodes = pickle.dumps(set())
        r.hset(block_id, 'nodes', nodes)
        i += 1
        push_block(block, block_id, get_available_nodes(), socketio)


def rebuild_file(password, blocks):
    master = ''
    for block in blocks:
        # print('block before: ', block)
        # print('block after: ', block.decode())
        master += block.decode()
    plaintext = decrypt(password, master.encode())
    return plaintext


def pull_file(name, password, sio):
    r = redis.Redis()
    if r.hgetall('file-'+name) is None:
        return 'File Not Found'
    redis_data = r.hgetall('file-'+name)
    blocks = pull_blocks(redis_data, sio)
    file = rebuild_file(password, blocks)
    return base64_to_file(file)


def pull_blocks(data, sio):
    r = redis.Redis()
    blocks = []
    blocks_num = len(data)
    for i in range(blocks_num):
        r.set('block_data', '')
        block_id = data[('block'+str(i)).encode()]
        block_hash = r.hget(block_id, 'hash')
        nodes = pickle.loads(r.hget(block_id, 'nodes'))
        block = pull_block(block_id, block_hash, nodes, sio)
        blocks.insert(i, block)
    return blocks


def pull_block(block_id, block_hash, nodes, sio):
    while True:
        r = redis.Redis()
        node_id = nodes.pop()
        socket = r.hget('nodes', node_id)
        sio.emit('send_block', block_id.decode(), room=socket)
        while True:
            block = r.get('block_data')
            if block == b'':
                time.sleep(0.1)
            elif md5_crypt.verify(block, block_hash):
                return block
            else:
                break


def test_encryption_decryption():
    plaintext = 'dank memes my dude'.encode()
    password = 'ya hate to see it!@$'
    data = encrypt(password, plaintext)
    return decrypt(password, data)


def get_available_nodes():
    r = redis.Redis()
    nodes = r.hkeys('nodes')
    if nodes is None:
        return []
    return nodes


def add_node(uid, socket):
    r = redis.Redis()
    r.hset('nodes', uid, socket)


def add_socket(uid, socket):
    r = redis.Redis()
    r.hset('sockets', socket, uid)


def rem_socket(uid):
    r = redis.Redis()
    socket = r.hget('nodes', uid)
    if socket is not None:
        r.hdel('sockets', socket)


def push_block(block, blockid, nodes, socketio):
    r = redis.Redis()
    for node in nodes:
        # Add node to the list of who's holding the block
        mems = pickle.loads(r.hget(blockid, 'nodes'))
        mems.add(str(node))
        r.hset(blockid, 'nodes', pickle.dumps(mems))
        sock = r.hget('nodes', node)
        socketio.emit('add_block', {"id": blockid, "data": block}, room=sock.decode())


def handle_response(res):
    blocks = res['blocks']
    for block_id, block_hash in blocks.items():
        #print('Block ID: ' + block_id + ' Hash: ' + block_hash)
        return
