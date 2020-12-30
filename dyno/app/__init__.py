# -*- coding: utf-8 -*-

# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
"""
Application setup and initlization
"""
import os
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
from werkzeug.utils import import_string
from . import cfg

def _env_init(app_env):
    """
    Select the proper configuration class from the `cfg` module and return it
    for use in application initlization.

    Note
    ----
    This function has the side effect of printing to the console in some cases.

    Parameters
    ----------
    app_env : str
        An application environment to run in. Must be either `test`, `dev` or `prod`.
        Otherwise, an exception will be thrown.

    Returns
    -------
    obj
        An object suitable for use in configuring Flask. Typically used with Flask().config.from_object()

    Raises
    ------
    Exception
        If the type of environment is not recognized, an exception of type Exception will be raised.

    Examples
    --------
    Create a Flask object and give it a configuration

    >>> app = Flask(__name__)
    >>> config_class = _env_init(app_env)
    >>> app.config.from_object(config_class)

    """
    if app_env == 'test':
        print('\n\n\033[1;33;40m ** Starting with test configuration ** \033[m \n\n')
        return import_string('dyno.app.cfg.TestingConfig')()

    elif app_env == 'dev':
        print('\n\n\033[1;33;40m ** Starting with development configuration ** \033[m \n\n')
        return import_string('dyno.app.cfg.DevelopmentConfig')()

    elif app_env == 'prod':
        return import_string('dyno.app.cfg.ProductionConfig')()
    else:
        raise Exception('Must specify valid app_env when calling create_app()')


def create_app(app_env='prod'):
    """
    This the main entrypoint for the Flask application.

    Parameters
    ----------
    app_env : str
        An application environment to run in. Must be either `test`, `dev` or `prod`.

    Returns
    -------
    obj
        A initialized Flask application
    """
    config_class = _env_init(app_env)

    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)
    from .api import bp as api_bp  # noqa E402
    app.register_blueprint(api_bp, url_prefix=app.config['API_PREFIX'])
    return app

app = create_app()
socketio = SocketIO(app, cors_allowed_origins=app.config['CORS_ORIGINS'])

@app.route('/log')
def index():
    return render_template("index.html")
