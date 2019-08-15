#!/bin/bash
redis-server redis.conf
cd src
python3 app.py
