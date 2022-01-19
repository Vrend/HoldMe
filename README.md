# HoldMe
Decentralized Storage - Inspired by Hivemind, written in Python


## Dependencies

1. Python 3
2. flask
3. redis-py
4. passlib
5. eventlet
6. flask-socketio
7. pycryptodome

## Docker Demo

This app has a docker image (vrend/holdme)

Run it with this command `docker run -d -p your_port:5000 vrend/holdme`

The Authentication code is "holdme"

## How to Use

1. Clone the repository, install the dependencies, and install redis

2. Create a file named "config" and fill it out (see section below)

3. Run redis using the provided configuration 'redis.conf'

4. Run `python3 app.py`

### Config file
```
1. Secret key (can be anything)
2. Your authentication code (password to access file page)
3. Enable debug mode (true or false)
```

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.

*Copyright © 2019 Vrend*
