#!/bin/bash
cd A_2/frontend && gunicorn --bind 0.0.0.0:5000 --workers 2 --worker-class gevent run:front&
cd A_2/managerapp && python3 run.py&
cd A_2/autoscaler && gunicorn --bind 0.0.0.0:5003 --workers 1 --timeout 300 run:scaler