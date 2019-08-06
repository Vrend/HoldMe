from flask import Flask, request, render_template
from authentication import *

app = Flask(__name__)

lock = ''


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/node')
def node():
    return 'Node page'


@app.route('/files')
@is_logged_in
def files():
    file_id = request.args.get('id', '')
    if file_id == '':
        return 'This is the file list'
    else:
        return 'This is file with id: ' + file_id


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


if __name__ == '__main__':
    config = get_config()
    app.secret_key = config[0]
    lock = config[1]
    app.run(debug=True)
