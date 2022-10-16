#!/bin/bash
cd frontend && gunicorn --bind 0.0.0.0:5000 front&
cd memcache && gunicorn --bind 0.0.0.0:5001 mem