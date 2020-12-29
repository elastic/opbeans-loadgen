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

import multiprocessing
import pytest
import requests
from flask import url_for

# https://github.com/pytest-dev/pytest-flask/issues/104#issuecomment-577908228
multiprocessing.set_start_method("fork")

API_GET_ENDPOINTS = ['api.get_list', 'api.get_scenarios']

@pytest.mark.usefixtures('live_server')
#@pytest.mark.usefixtures("default_session")
@pytest.mark.parametrize('endpoint', API_GET_ENDPOINTS)
def test_server_control_http_code(endpoint):
    """
    GIVEN a running application
    WHEN the client makes a valid request to the API endpoints
    THEN the server responds with a HTTP 200
    """
    res = requests.get(url_for(endpoint, _external=True))
    assert res.status_code == 200


