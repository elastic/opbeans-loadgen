# -*- coding: utf-8 -*-
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
from app.cfg import Config as Cfg


def create_app(config_class=Cfg):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)
    return app


app = create_app()
socketio = SocketIO(app, cors_allowed_origins=['http://localhost:9000', 'http://localhost:5000'])


from app.api import bp as api_bp  # noqa E402
app.register_blueprint(api_bp, url_prefix='/api')


@app.route('/log')
def index():
    return render_template("index.html")
