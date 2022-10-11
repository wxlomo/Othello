"""
 * __init__.py
 * Front-end constructor
 *
 * Author: Weixuan Yang, Haotian Chen, Haozhe Sun
 * Date: Oct. 11, 2022
"""
from flask import Flask

global memcache

gallery = Flask(__name__)
