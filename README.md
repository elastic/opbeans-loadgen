[![Build Status](https://apm-ci.elastic.co/buildStatus/icon?job=apm-agent-python%2Fopbeans-loadgen-mbp%2Fmaster)](https://apm-ci.elastic.co/job/apm-agent-python/job/opbeans-loadgen-mbp/job/master/)

# Opbeans Load Generator

## Summary

This is a load generator for [Opbeans](https://github.com/elastic?utf8=%E2%9C%93&q=Opbeans&type=&language=) as a Docker container.

It has two primary modes of operation -- either as a stand-alone container which can generate load based on environment variables present at runtime or as a long-running web service which can receive commands to control load-generation over a HTTP REST interface.

Load is generated through invocation of `molotov` which is a load-generation tool provided by [the Molotov project](https://molotov.readthedocs.io).

## Standalone mode
### Running

Start the docker container with a list of base URLs to generate load on

    > docker run --rm -e OPBEANS_URLS=opbeans-node:http://opbeans-node:3000,opbeans-python:http://opbeans-python:3000 opbeans/opbeans-loadgen

## HTTP mode
The use of HTTP mode was developed specifically as a load-generation component for use in the [APM Integration Test](https://github.com/elastic/apm-integration-testing) suite. 

Specifically, it is designed for use when the suite is launched using the `--dyno` flag, which enables user-controlled load-testing with the ability to manipulate the performance constraints of various services at-will.

### Running in HTTP mode in a container [Recommended]
To run the Opbeans Load Generator in HTTP mode, start the container by defining the environment variable `WS` in the context of the running container. Typically, this is done using the `-e` flag [as shown in the Docker documentation](https://docs.docker.com/compose/environment-variables/#pass-environment-variables-to-containers).

#### Note on running in the APM Integration Test Suite
When running the Opbeans Load Generator in the APM Integration Test suite with the `--dyno` flag, the `WS` environment variable will be defined automatically and the container will start in HTTP mode.

### HTTP method overview

The following is a list of HTTP methods and their purpose. For specifics including possible
arguments and expected returns, please see the in-line documentation:

Endpoint|HTTP Verb|Description
--------|---------|-----------
/api/start|POST|Start a load-generation job
/api/list|GET|List all configured jobs
/api/update|POST|Updates a running job with a new configuration
/api/stop|GET|Stops a currently-running load-generation job
/api/scenarios|GET|Retreive a list of scenarios

### Further discussion

For further discussion, please see the detailed documentation in the `README` that is included in the `/dyno` directory.

## Testing locally

The simplest way to run all tests for this project is by running:

```bash
> make test
```

## Types of tests
### BATS

Tests are written using [BATS](https://github.com/sstephenson/bats) under the `/tests` dir.
### Pytest
To run the Python tests, one must first install the test requirements:
```bash
> pip install requirements-dev.txt
```

This project includes a [pytest](http://docs.pytest.org/en/latest/) test suite which provides a set of unit and functional tests.

To run these tests, both `pytest` and the `pytest-flask` modules must be installed and available to Python.


## Publishing to Docker Hub locally

Publish the docker image with

```bash
> VERSION=1.2.3 make publish
```

NOTE: VERSION refers to the tag for the docker image which will be published in the registry
