#!/bin/bash
cd ~/ECE1779-Group9-Project-Code/A_2/memcache && gunicorn --bind 0.0.0.0:5001 --workers 1 run:mem