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
Functional Tests for the Openbeans Load Generator
"""
import os
import subprocess

def _root_dir():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_dir, '../../')


def test_command_execution():
    """
    GIVEN a call to generate_procfile.py from the shell
    WHEN arguments for URLs, RPMs, and RLS are provided
    THEN the command will produce output with the corresponding values set
    """
    gen_procfile_script = os.path.join(_root_dir(), 'generate_procfile.py')
    proc = subprocess.run(
            [
                'python',
                gen_procfile_script,
                "opbeans-python:http://opbeans-python:3000",
                "opbeans-python:500",
                "opbeans-python:500"
                ],
            stdout=subprocess.PIPE
            )

    assert proc.stdout == b'python: OPBEANS_BASE_URL=http://opbeans-python:3000 OPBEANS_NAME=opbeans-python molotov -v --duration 500 --delay 0.120 --uvloop molotov_scenarios.py\n'

def test_entrypoint_execution(default_environment):
    """
    GIVEN a call to the entrypoint script
    WHEN the enviornment variables are set for URLS, RPMS, and RLS
    THEN the command will produce output with the corresponding values set
    """
    entrypoint_script = os.path.join(_root_dir(), 'entrypoint.sh')
    procfile = os.path.join(_root_dir(), 'Procfile')

    if os.path.exists(procfile):
        os.remove(procfile)

    proc = subprocess.run(entrypoint_script, stdout=subprocess.PIPE, cwd=_root_dir())

    with open(procfile, 'r') as fh_:
        procfile_data = fh_.readline()
    assert procfile_data == 'python: OPBEANS_BASE_URL=http://opbeans-python:3000 OPBEANS_NAME=opbeans-python molotov -v --duration 500 --delay 0.120 --uvloop molotov_scenarios.py\n'
