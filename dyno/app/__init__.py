# -*- coding: utf-8 -*-
from flask import Flask, render_template
from flask_socketio import SocketIO
from app.cfg import Config as Cfg


def create_app(config_class=Cfg):
    app = Flask(__name__)
    app.config.from_object(config_class)
    return app


app = create_app()
socketio = SocketIO(app)

from app.api import bp as api_bp  # noqa E402
app.register_blueprint(api_bp, url_prefix='/api')


@app.route('/log')
def index():
    return render_template("index.html")
