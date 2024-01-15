#!/bin/bash

cd /etc/clash-config
gunicorn -w 4 -b 0.0.0.0:6789 server:app
