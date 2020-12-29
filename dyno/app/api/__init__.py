# -*- coding: utf-8 -*-
from flask import Blueprint

bp = Blueprint('api', __name__)

from . import control  # noqa E402
