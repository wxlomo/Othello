#!/bin/bash
cd frontend && gunicorn --bind 0.0.0.0:5000 --workers 12 run:front&
cd memcache && gunicorn --bind 0.0.0.0:5001 --workers 12 run:mem