#!../venv/bin/python
from frontend import front
from memcache import mem

front.run('0.0.0.0', port=5000, debug=True)
mem.run('0.0.0.0', port=5001, debug=True)


