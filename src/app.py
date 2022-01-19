import eventlet
eventlet.monkey_patch()
from flask import Flask, request, render_template, send_file
from flask_socketio import SocketIO, send, emit
from authentication import *
from database import *
import threading
import uuid
import time
import redis as red
import io
from passlib.hash import md5_crypt

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')
lock = ''
thread = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/node')
def node():
    return render_template('node.html')


@app.route('/delete', methods=['POST'])
@is_logged_in
def delete():
    file_id = request.args.get('id', '')

    if file_id == '' or not check_if_file_exists(file_id):
        return redirect(url_for('files'))

    delete_file(file_id, socketio)
    return redirect(url_for('files'))


@app.route('/deleteall', methods=['POST'])
@is_logged_in
def delete_all():
    delete_files(socketio)
    return redirect(url_for('deauthenticate'))


@app.route('/files', methods=['GET', 'POST'])
@is_logged_in
def files():
    file_id = request.args.get('id', '')
    if request.method == 'POST':
        if 'single_file' in request.form:
            password = request.form['password']
            data = pull_file(file_id, password, socketio)
            if data == 'Bad Password':
                return 'Bad Password'
            return send_file(io.BytesIO(data[2]), as_attachment=True, attachment_filename=data[0], mimetype=data[1])
        else:
            file = request.files['file']
            name = request.form['name']
            password = request.form['password']
            if file.filename == '' or name == '' or password == '':
                return render_template('files.html', files=get_files())
            push_file(name, password, file, file.filename, socketio)
            return redirect(url_for('files'))

    if file_id == '':
        return render_template('files.html', files=get_files())
    elif not check_if_file_exists(file_id):
        return redirect(url_for('files'))
    else:
        return render_template('file.html', id=file_id)


@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    if request.method == 'POST':
        key = request.form['password']
        if key == lock:
            session['logged_in'] = True
            return redirect(url_for('index'))

    return render_template('authenticate.html')


@app.route('/deauthenticate')
@is_logged_in
def deauthenticate():
    session.clear()
    return redirect(url_for('index'))


# Generic socket catchers
@socketio.on('message')
def handle_message(message):
    send(message)
    print('Received message: ' + message)


@socketio.on('json')
def handle_json(json):
    send(json, json=True)
    print('received json: ' + str(json))


# Custom example
@socketio.on('connect')
def handle_connect():
    global thread
    print('Client Socket SID: ' + request.sid)
    if thread is None:
        thread = threading.Thread(target=heartbeat)
        thread.daemon = True
        thread.start()


@socketio.on('on_connect')
def handle_on_connect(res):
    data = res['id']
    if data == 'none':
        client_id = str(uuid.uuid1())
        add_node(client_id, request.sid)
        add_socket(client_id, request.sid)
        emit('give_uid', client_id)
    else:
        rem_socket(data)
        add_node(data, request.sid)
        add_socket(data, request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    print('Client Disconnected')
    r = red.Redis()
    keys = r.hkeys('nodes')
    for key in keys:
        if r.hget('nodes', key) == request.sid:
            r.hdel('nodes', key)
            return


def heartbeat():
    r = red.Redis()
    while True:
        time.sleep(5)
        r.set('check', 'true')
        socketio.emit('heartbeat')
        time.sleep(5)
        r.set('check', 'false')
        blocks = r.hkeys('confirm_blocks')
        for block in blocks:
            block_id = block.decode()
            set_id = r.hget('confirm_blocks', block_id).decode()
            nodes = r.smembers(set_id)
            pickled_nodes = pickle.dumps(nodes)
            r.hset(block_id, 'nodes', pickled_nodes)
            if len(nodes) < MINIMUM_NODES:
                t = threading.Thread(target=propagate_block, args=(block_id, len(nodes), socketio))
                t.start()
        r.delete('confirm_blocks')


@socketio.on('heartbeat_resp')
def handle_heartbeat_resp(json):
    if 'id' in json:
        handle_response(json)
    else:
        emit('force_disconnect', room=request.sid)


@socketio.on('receive_block')
def get_block(json):
    r = red.Redis()
    block = json['block']
    block_id = json['id']
    block_hash = r.hget(block_id, 'hash')
    if block_hash is None:
        return
    if md5_crypt.verify(block, block_hash):
        r.hset('temp_data', block_id, block)
    else:
        r.hset('temp_data', block_id, 'Block Not Found')


@socketio.on('receive_block_propagate')
def get_block_propagate(json):
    r = red.Redis()
    block = json['block']
    block_id = json['id']
    block_hash = r.hget(block_id, 'hash')
    if block_hash is None:
        return
    if md5_crypt.verify(block, block_hash):
        r.set('temp_data_'+block_id, block)
    else:
        r.set('temp_data_'+block_id, 'Block Not Found')


@app.errorhandler(404)
def handle_404(error):
    print(error)
    return redirect(url_for('index'))


if __name__ == '__main__':
    config = get_config()
    app.secret_key = config[0]
    lock = config[1].strip()
    if not test_redis():
        print('Connection with redis failed. Make sure redis is running.')
        sys.exit(1)
    socketio.run(app, debug=config[2], host='0.0.0.0')
