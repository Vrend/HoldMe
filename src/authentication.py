import sys
from functools import wraps
from flask import session, redirect, flash, url_for


# Wrappers for sessions
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Not logged in', 'danger')
            return redirect(url_for('index'))
    return wrap


def get_config():
    try:
        file = open('../config', 'r')
    except FileNotFoundError:
        print('Config file doesn\'t exist, exiting...')
        sys.exit(1)

    secret = file.readline()
    lock = file.readline()

    if secret == '' or lock == '':
        print('Config file not configured correctly, exiting...')
        sys.exit(1)
    else:
        print('Loading configuration...')

    return [secret, lock]
