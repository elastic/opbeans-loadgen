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

import pytest


@pytest.fixture
def default_environment(monkeypatch):
    """
    Set up default variables to produce a functional
    test environment
    """
    monkeypatch.setenv("OPBEANS_URLS", "opbeans-python:http://opbeans-python:3000")
    monkeypatch.setenv("OPBEANS_RPMS", "opbeans-python:500")
    monkeypatch.setenv("OPBEANS_RLS", "opbeans-python:500")
