from flask import Flask, request, render_template
from flask_socketio import SocketIO, send, emit
from authentication import *
from database import *

app = Flask(__name__)
socketio = SocketIO(app)
lock = ''


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/node')
def node():
    return render_template('node.html')


@app.route('/redis')
def redis():
    return test_redis()


@app.route('/files', methods=['GET', 'POST'])
@is_logged_in
def files():
    if request.method == 'POST':
        if 'single_file' in request.form:
            return render_template('files.html')
        else:
            file = request.files['file']
            name = request.form['name']
            if file.filename == '' or name == '':
                return render_template('files.html')
            push_file(name, file)
            return render_template('files.html')

    file_id = request.args.get('id', '')
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
    print('Client Socket SID: ' + request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    print('Client Disconnected')


@socketio.on('heartbeat_resp')
def handle_heartbeat_resp(json):
    handle_response(json)


def heartbeat():
    socketio.emit('heartbeat')


@app.errorhandler(404)
def handle_404(error):
    print(error)
    return redirect(url_for('index'))


if __name__ == '__main__':
    config = get_config()
    app.secret_key = config[0]
    lock = config[1].strip()
    socketio.run(app, debug=config[2])
