#!/bin/bash
cd A_3/frontend && gunicorn --bind 0.0.0.0:5000 --workers=3 run:front