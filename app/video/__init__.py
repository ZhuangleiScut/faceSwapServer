#! /usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint
video = Blueprint('video', __name__)
from . import views, errors
