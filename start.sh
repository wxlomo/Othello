#!/bin/sh
flask --app frontend --port=5000 & flask --app memcache run --port=5001