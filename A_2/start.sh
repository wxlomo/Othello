#!/bin/bash
cd frontend && gunicorn --bind 0.0.0.0:5000 --workers 3 --worker-class gevent run:front&
cd managerapp && gunicorn --bind 0.0.0.0:5002 --workers 1 run:manager&
cd autoscaler && gunicorn --bind 0.0.0.0:5003 --workers 1 run:scaler