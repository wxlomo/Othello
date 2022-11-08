"""
 * __init__.py
 * managerapp instance constructor
 *
 * Author: Haotian Chen
 * Date: Nov. 8, 2022
"""
from flask import Flask

front = Flask(__name__)

from . import managerapp
