"""
 * __init__.py
 * Front-end instance constructor
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
"""
from flask import Flask
from app import front

gallery = Flask(__name__)
