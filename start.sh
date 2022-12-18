#!/bin/bash
cd A_3/frontend && gunicorn --bind 127.0.0.1:5000 --workers 3 run:front