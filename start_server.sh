#!/usr/bin/env bash
export FLASK_APP=run.py
export FLASK_DEBUG=1
flask run --with-threads --host=0.0.0.0