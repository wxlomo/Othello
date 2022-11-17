#!/bin/bash
cd frontend && gunicorn --bind 0.0.0.0:5000 --workers 2 --worker-class gevent run:front&
cd managerapp && gunicorn --bind 0.0.0.0:5002 --workers 2 --worker-class gevent run:manager&
cd autoscaler && gunicorn --bind 0.0.0.0:5003 --workers 1 run:scaler