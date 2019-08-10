import eventlet
eventlet.monkey_patch()
from flask import Flask, request, render_template
from flask_socketio import SocketIO, send, emit
from authentication import *
from database import *
import threading
import uuid
import time
import redis as red

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


@app.route('/redis')
def redis():
    return test_redis()


@app.route('/enc')
def enc():
    return test_encryption_decryption()


@app.route('/files', methods=['GET', 'POST'])
@is_logged_in
def files():
    file_id = request.args.get('id', '')
    if request.method == 'POST':
        if 'single_file' in request.form:
            password = request.form['password']
            pull_file(file_id, password, socketio)
            return render_template('files.html')
        else:
            file = request.files['file']
            name = request.form['name']
            password = request.form['password']
            if file.filename == '' or name == '' or password == '':
                return render_template('files.html')
            push_file(name, password, file, socketio)
            return render_template('files.html')

    if file_id == '':
        return render_template('files.html')
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
    while True:
        time.sleep(10)
        r = red.Redis()
        socketio.emit('heartbeat')


@socketio.on('heartbeat_resp')
def handle_heartbeat_resp(json):
    if 'id' in json:
        handle_response(json)


@socketio.on('receive_block')
def get_block(json):
    r = red.Redis()
    block = json['block']
    r.set('block_data', block)


@app.errorhandler(404)
def handle_404(error):
    print(error)
    return redirect(url_for('index'))


if __name__ == '__main__':
    config = get_config()
    app.secret_key = config[0]
    lock = config[1].strip()
    socketio.run(app, debug=config[2])
