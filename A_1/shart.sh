#!/bin/bash
cd frontend && flask run --host=0.0.0.0 --port=5000 &
cd memcache && flask run --host=0.0.0.0 --port=5001