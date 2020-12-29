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
    with mock.patch('dyno.app.api.control._launch_job') as job_launcher_mock:
        res = client.post(url_for('api.start_job'), json=query)
    job_launcher_mock.assert_called_with('test-job', '999', '1234', '4321', '3', 'scenarios/test_scenario.py', '0', '2', 'foo_label')
    assert res.json == {}

def test_update_no_job(client):
    """
    GIVEN a request that does not specify a job
    WHEN the request is sent to the /update endpoint
    THEN the endpoint bails out and returns an empty response
    """
    res = client.post(url_for('api.update_job'))
    assert res.status_code == 400

def test_update(client, job_status):
    """
    GIVEN an HTTP client
    WHEN the client requests /api/update to update a job
    THEN the job is updated
    """
    post_data = {
            'job': 'python',
            'workers': 990,
            'error_weight': 991,
            'label_weight': 992,
            'label_name': 'fake_label_name'
            }
    with mock.patch.dict('dyno.app.api.control.JOB_STATUS', job_status):
        with mock.patch('dyno.app.api.control._stop_job') as stop_job_mock:
            with mock.patch('dyno.app.api.control._launch_job') as launch_job_mock:
                with mock.patch('dyno.app.api.control._update_status') as update_status_mock:
                    client.post(url_for('api.update_job'), json=post_data)

    stop_job_mock.assert_called_with('python')
    job_caller_stub = mock.call('python', '990', '991', '992', 990, 'fake_scenario', 991, 992, 'fake_label_name')
    launch_job_mock.assert_has_calls( [job_caller_stub] )
    update_status_mock.assert_has_calls( [job_caller_stub] )

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
    assert ret.json == {}

@mock.patch('socketio.client.Client.emit')
@mock.patch('dyno.app.api.control._construct_toxi_env')
@mock.patch('dyno.app.api.control._update_status')
@mock.patch('subprocess.Popen')
def test_launch_job(proc_mock, update_status_mock, toxi_env_mock, socketio_mock):
    """
    GIVEN a sane set of arguments
    WHEN the _launc_job() function is called
    THEN a job is launched
    """
    dyno.app.api.control._launch_job(
        'python',
        '990',
        '991',
        '992',
        '993',
        'fake_scenario',
        '994'
        )
    assert socketio_mock.caled_with('service_state', {'data': {'python': 'start'}})
    assert toxi_env_mock.called_with('python', '990', 'fake_scenario', '994')
    assert update_status_mock.called_with(
            'python',
            '990',
            '991',
            '992',
            '993',
            'fake_scenario',
            '994',
            None,
            None
            )
    assert proc_mock.call_args[0][0] == [
            '/app/venv/bin/python',
            '/app/venv/bin/molotov',
            '-v',
            '--duration',
            '991',
            '--delay',
            '992',
            '--uvloop',
            '--workers',
            '993',
            '--statsd',
            '--statsd-address',
            'udp://stats-d:8125',
            'fake_scenario'
            ]
    [0]



@mock.patch.dict('os.environ', {}, clear=True)  # Assure a clean env
def test_construct_toxi_env():
    """
    GIVEN an environment which contains data about the opbeans
    WHEN we ask for a dictionary describing the environment
    THEN the returned dictionary reflects the configured environment
    """
    ret = dyno.app.api.control._construct_toxi_env('fake-job', 9999, 'fake_scenario', 99)
    assert ret == {
            'OPBEANS_BASE_URL': "http://toxi:9999",
            'OPBEANS_NAME': 'opbeans-fake-job',
            'ERROR_WEIGHT': '99'
            }

