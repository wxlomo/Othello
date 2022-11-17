#!/bin/bash
cd A_1/frontend && gunicorn --bind 0.0.0.0:5000 --workers 3 --worker-class gevent run:front&
cd A_1/memcache && gunicorn --bind 0.0.0.0:5001 --workers 3 run:mem