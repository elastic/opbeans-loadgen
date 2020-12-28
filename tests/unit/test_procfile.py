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
Tests for the Openbeans Load Generator
"""
from unittest import mock
import generate_procfile


def test_single_url():
    """
    GIVEN a request to create a Procfile for a single URL
    WHEN the request is issued
    THEN the output contains a configuration for the URL
    """
    with mock.patch('sys.stdout.write') as fake_sys:
        generate_procfile.create_procfile("opbeans-python:http://opbeans-python:3000")  # noqa E501
        fake_sys.assert_called_with(
                'python: OPBEANS_BASE_URL=http://opbeans-python:3000 OPBEANS_NAME=opbeans-python molotov -v --duration 31536000 --delay 0.600 --uvloop molotov_scenarios.py\n')  # noqa E501


def test_multiple_urls():
    """
    GIVEN a request to create a Procfile with multiple URLs
    WHEN the request is issued
    THEN the output contains configuration for both URLs
    """
    with mock.patch('sys.stdout.write') as fake_sys:
        generate_procfile.create_procfile("opbeans-python:http://opbeans-python:3000,opbeans-java:http://opbeans-java:4000")  # noqa E501
    assert fake_sys.call_count == 2

    python_call = mock.call('python: OPBEANS_BASE_URL=http://opbeans-python:3000 OPBEANS_NAME=opbeans-python molotov -v --duration 31536000 --delay 0.600 --uvloop molotov_scenarios.py\n')  # noqa E501
    java_call = mock.call('java: OPBEANS_BASE_URL=http://opbeans-java:4000 OPBEANS_NAME=opbeans-java molotov -v --duration 31536000 --delay 0.600 --uvloop molotov_scenarios.py\n')  # noqa E501

    fake_sys.assert_has_calls([python_call, java_call])


def test_with_rpm():
    """
    GIVEN a request to create a Procfile which includes a rpm_env value
    WHEN the request is issued
    THEN the `delay` flag in the output is adjusted accordingly
    """
    with mock.patch('sys.stdout.write') as fake_sys:
        generate_procfile.create_procfile("opbeans-python:http://opbeans-python:3000", rpm_env_string="opbeans-python:500")  # noqa E501
    fake_sys.assert_called_with('python: OPBEANS_BASE_URL=http://opbeans-python:3000 OPBEANS_NAME=opbeans-python molotov -v --duration 31536000 --delay 0.120 --uvloop molotov_scenarios.py\n')  # noqa E501


def test_with_rls():
    """
    GIVEN a request to create a Procfile which contains a RLS value
    WHEN the request is issued
    THEN the `duration` flag in the output is adjusted accordingly 
    """
    with mock.patch('sys.stdout.write') as fake_sys:
        generate_procfile.create_procfile("opbeans-python:http://opbeans-python:3000", rls_env_string="opbeans-python:500")  # noqa E501
    fake_sys.assert_called_with('python: OPBEANS_BASE_URL=http://opbeans-python:3000 OPBEANS_NAME=opbeans-python molotov -v --duration 500 --delay 0.600 --uvloop molotov_scenarios.py\n')  # noqa E501
