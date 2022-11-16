#!/bin/bash
cd managerapp && gunicorn --bind 0.0.0.0:5002 --workers 1 run:manager&
cd autoscaler && gunicorn --bind 0.0.0.0:5003 --workers 1 run:scaler