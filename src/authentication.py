import sys
from functools import wraps
from flask import session, redirect, url_for


# Wrappers for sessions
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap


# Grabs data from config file at startup
def get_config():
    try:
        file = open('../config', 'r')
    except FileNotFoundError:
        print('Config file doesn\'t exist, exiting...')
        sys.exit(1)

    secret = file.readline()
    lock = file.readline()
    debug = file.readline()

    if secret == '' or lock == '' or debug == '':
        print('Config file not configured correctly, exiting...')
        sys.exit(1)
    else:
        print('Loading configuration...')

    if debug == 'true':
        debug = True
    else:
        debug = False

    return [secret, lock, debug]
