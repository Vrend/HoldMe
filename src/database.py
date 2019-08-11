import textwrap
from encryption import *
import uuid
import redis
from passlib.hash import md5_crypt
import pickle
import time
import mimetypes
import threading

BLOCK_SIZE = 1024

OPTIMAL_NODES = 20

MINIMUM_NODES = 10


def file_to_base64(file):
    return base64.b64encode(file.read())


def base64_to_file(string):
    return base64.b64decode(string)


def push_file(name, password, file, filename, socketio):
    r = redis.Redis()
    mimetype = mimetypes.MimeTypes().guess_type(filename)[0]
    if mimetype is None:
        mimetype = 'application/octet-stream'
    base = file_to_base64(file)
    plaintext = filename.encode() + b'mimetype:' + mimetype.encode() + b'filedata:' + base
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
    if file == 'Bad Password':
        return file
    plaintext = file.split(b'mimetype:')
    name = plaintext[0].decode()
    plaintext = plaintext[1].split(b'filedata:')
    mime = plaintext[0].decode()
    file = base64_to_file(plaintext[1])
    return name, mime, file


def pull_blocks(data, sio):
    r = redis.Redis()
    blocks = []
    blocks_num = len(data)
    for i in range(blocks_num):
        r.set('block_data', '')
        block_id = data[('block'+str(i)).encode()]
        nodes = pickle.loads(r.hget(block_id, 'nodes'))
        nodes_copy = nodes.copy()
        t = threading.Thread(target=pull_block, args=(block_id, nodes_copy, sio))
        t.start()
    while len(r.hkeys('temp_data')) != blocks_num:
        time.sleep(0.1)
    for i in range(blocks_num):
        block_id = data[('block'+str(i)).encode()]
        block = r.hget('temp_data', block_id)
        blocks.insert(i, block)
    r.delete('temp_data')
    return blocks


def pull_block(block_id, nodes, sio):
    while True:
        r = redis.Redis()
        node_id = nodes.pop()
        socket = r.hget('nodes', node_id)
        sio.emit('send_block', block_id.decode(), room=socket)
        while True:
            if r.hexists('temp_data', block_id):
                if r.hget('temp_data', block_id) == b'Block Not Found':
                    break
                else:
                    return
            else:
                time.sleep(0.1)


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


def check_if_file_exists(file_id):
    r = redis.Redis()
    return r.exists('file-' + file_id) == 1


def get_files():
    files = []
    r = redis.Redis()
    for file in r.scan_iter(match='file*'):
        files.append(file.decode().split('file-')[1])
    return files


def delete_file(file_id, socketio):
    r = redis.Redis()
    file = r.hgetall('file-'+file_id)
    for i in range(len(file)):
        block_id = file[('block'+str(i)).encode()]
        flush_block(block_id, socketio)
        r.delete(block_id)
    r.delete('file-'+file_id)


def delete_files(socketio):
    r = redis.Redis()
    for file in r.scan_iter(match='file*'):
        file_id = file.decode().split('file-')[1]
        delete_file(file_id, socketio)


def flush_block(block_id, socketio):
    r = redis.Redis()
    nodes = pickle.loads(r.hget(block_id, 'nodes'))
    for node in nodes:
        node = node.split('b\'')[1][:-1]
        sock = r.hget('nodes', node)
        socketio.emit('flush_block', block_id.decode(), room=sock.decode())
