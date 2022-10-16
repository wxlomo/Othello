#!/bin/bash
cd frontend && gunicorn --bind 0.0.0.0:5000 run:front&
cd memcache && gunicorn --bind 0.0.0.0:5001 run:mem