#!/bin/bash gunicorn --bind 0.0.0.0:5002 --workers 4 --worker-class gevent run:manager
cd frontend && gunicorn --bind 0.0.0.0:5000 --workers 2 --worker-class gevent run:front&
cd managerapp && python3 run.py&
cd autoscaler && gunicorn --bind 0.0.0.0:5003 --workers 1 run:scaler