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
Tests for the Openbeans Dyno
"""
import dyno.app.api.control
from unittest import mock
from flask import url_for

def test_scenarios(client, scenarios):
    """
    GIVEN an HTTP client
    WHEN the client requests /api/scenarios
    THEN it receives back a list of active scenarios
    """
    res = client.get(url_for('api.get_scenarios'))
    assert res.json == {'scenarios': scenarios}


def test_start(client):
    """
    GIVEN an HTTP client
    WHEN the client requests /api/start with arguments
    THEN a load-generation job is started with those arguments
    """
    query = {
            'job': 'test-job',
            'port': '999',
            'scenario': 'test_scenario',
            'duration': '1234',
            'delay': '4321'
            }
    with mock.patch('subprocess.Popen') as fake_popen:
        with mock.patch('socketio.client.Client.emit') as fake_socketio:
            with mock.patch.dict('dyno.app.api.control.JOB_STATUS', {'test-job': {'running': False}}):
                res = client.get(url_for('api.start_job'), query_string=query)

    # Here we assert against the call args because we don't care about tall the other stuff
    # that comes along for the ride with Popen, such as the environment
    assert fake_popen.call_args[0][0] == [
            '/app/venv/bin/python',
            '/app/venv/bin/molotov',
            '-v',
            '--duration',
            '1234',
            '--delay',
            '4321',
            '--uvloop',
            '--statsd',
            '--statsd-address',
            'udp://stats-d:8125',
            'test_scenario'
            ]
    fake_socketio.assert_called_with('service_state', {'data': {'test-job': 'start'}})
    assert res.json == {}

 
def test_stop(client):
    """
    GIVEN an HTTP client
    WHEN the client requests /api/stop with arguments
    THEN the request to stop the job is fufilled
    """
    pid_mock = mock.patch('os.getpgid', return_value='999')
    proc_mock = mock.create_autospec('subprocess.Popen')
    proc_mock.pid = 99999
    query = {'job': 'test-job'}
    with mock.patch('socketio.client.Client.emit') as fake_socketio:
        with mock.patch.dict('dyno.app.api.control.JOB_STATUS', {'test-job': {'running': False}}):
            with mock.patch.dict('dyno.app.api.control.JOB_MANAGER', {'test-job': proc_mock}):
                with pid_mock:
                    with mock.patch('os.killpg') as kill_mock:
                        res = client.get(url_for('api.stop_job'), query_string=query)
    fake_socketio.assert_called_with('service_state', {'data': {'test-job': 'stop'}})
    kill_mock.assert_called()
    assert res.json == {}

def test_list(client, job_status):
    """
    GIVEN an abritrary set of job
    WHEN a client requests the /list endpoint
    THEN the client receives the list of jobs
    """
    ret = client.get(url_for('api.get_list'))
    assert ret.json == job_status

def test_configured_jobs(procfile, job_status):
    """
    GIVEN a Procfile
    WHEN fetch_configured_jobs is called
    THEN it returns a dictionary containing configured jobs
    """
    with mock.patch('dyno.app.api.open', mock.mock_open(read_data=procfile)):
        ret = dyno.app.api.control.fetch_configured_jobs()
    assert ret == job_status

@mock.patch.dict('os.environ', {}, clear=True)  # Assure a clean env
def test_construct_toxi_env():
    """
    GIVEN an environment which contains data about the opbeans
    WHEN we ask for a dictionary describing the environment
    THEN the returned dictionary reflects the configured environment
    """
    ret = dyno.app.api.control._construct_toxi_env('fake_job', 9999)
    assert ret == {
            'OPBEANS_BASE_URL': "http://toxi:9999",
            'OPBEANS_NAME': 'fake_job'
            }


