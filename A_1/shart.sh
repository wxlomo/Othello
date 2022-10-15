#!/bin/bash
cd frontend && flask run --port=5000 & 
cd memcache && flask run --port=5001