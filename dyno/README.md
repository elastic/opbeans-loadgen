[![Build Status](https://apm-ci.elastic.co/buildStatus/icon?job=apm-agent-python%2Fopbeans-loadgen-mbp%2Fmaster)](https://apm-ci.elastic.co/job/apm-agent-python/job/opbeans-loadgen-mbp/job/master/)

# Dyno Web Interface for Opbeans Load Generator

The Dyno Web Interface is designed for use with the APM Integration Test Suite when it is run in Dyno mode using the `--dyno` flag. 

When this flag is present, the Opbeans Load Generator is included as a running service and the Dyno web service is automatically enabled, allowing for on-demand load-generation to be controlled both programatically and directly by a user from a web interface.

## HTTP method overview

The following is a list of HTTP methods and their purpose. For specifics including possible arguments and expected returns, please see the in-line documentation:

Endpoint|HTTP Verb|Description
--------|---------|-----------
`/api/start`|`POST`|Start a load-generation job
`/api/list`|`GET`|List all configured jobs
`/api/update`|`POST`|Updates a running job with a new configuration
`/api/stop`|`GET`|Stops a currently-running load-generation job
`/api/scenarios`|`GET`|Retreive a list of scenarios

For specifics on arguments to the various endpoints, please see the in-line documentation.

## Integration with the APM Test Suite
When run as a part of the APM Integration Test Suite, the Dyno service also provides additional behavior.

### Socket responses
[SocketIO](https://socket.io/) is used to stream data about load-generation back to the client. In this application, SocketIO broadcasts are generally used in-lieu of direct returns when making requests to HTTP endpoints.

### Stats streaming
To facilitate the realtime streaming of stats about load generation, the `statsd` option [is integrated with Molotov](https://molotov.readthedocs.io/en/stable/cli/). 

## Scenarios

[Scenarios](https://molotov.readthedocs.io/en/stable/tutorial/#running-one-scenario) are the means through which the load-generator selects which URLs to apply to load to and at what frequency. They are written as pure Python scripts.

The Opbeans Load Generator project includes multiple scenarios out of the box. They are included in the `/scenarios` directory. Additional scenarios can be added there and will be immediately available to a running application without the need to restart.

Custom scenarios can include dynamic variables via the inclusion of certain environment variables which can control their behavior.

### Controlling scenario behavior
The following environment variables are supported inside scenarios:

Environment Variable|Description
--------------------|-----------
`SERVER_URL`|The target for load traffic
`SERVICE_NAME`|The type of service. Used to differentiate between the specific endpoints available in different opbeans. Ex: `opbeans-python`|`default`
`ERROR_WEIGHT`|Controls the frequency at which error pages are called
`LABEL_WEIGHT`|Controls the frequency at which specific labels are called. See `Labels` for more information.

## Labels

Certain Opbeans support the ability to hit an endpoint with a HTTP request which will result in a label being applied and an arbitrary amount of delay. The following applications include this support:

Opbean|Details
------|-------
`opbeans-python`|https://github.com/elastic/opbeans-python/pull/51

## Example Usage

Normally, this service simply runs as a container alonside others in the APM Integration Test Suite and is controlled by the `Dyno` control plane with the test suite is started with the `--dyno` flag.

However, it is also possible to interact with the Opbeans Load Generator directly.

If started via the APM Integration Test suite, by default the REST interface will be available at `http://localhost:8999`.

### Start a load-generation job

To start a load-generation job directed at the Python Opbean with default configuration.

```bash
❯ curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"job":"opbeans-python","port":"8000"}'\
  http://localhost:8999/api/start
```

### List the status of running jobs
```bash
❯ curl -s http://localhost:8999/api/list|jq
    {
      "python": {
        "delay": "0.600",
        "duration": "31536000",
        "error_weight": "0",
        "label_name": "foo_label",
        "label_weight": "2",
        "name": "python",
        "port": "8000",
        "running": false,
        "scenario": "scenarios/molotov_scenarios.py",
        "workers": "3"
      }
    }
```

### Increase the load on a service

Assuming the workers were previously set at the default of two, this rougly doubles the load targeted to the Python Opbean service.
```bash
❯ curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"job":"python","workers":4}'\
  http://localhost:8999/api/start
```

### Stop load-generation
```bash
> curl http://localhost:8999/api/stop?job=opbeans-python
```

### List available scenarios
```bash
        ❯ curl -s http://localhost:8999/api/scenarios|jq
        {
          "scenarios": [
            "dyno",
            "molotov_scenarios",
            "high_error_rates"
          ]
        }
```

## Logging and Troubleshooting
Flask will produce output on standard out by default. When deployed as a part of the APM Integration Test suite, the following will tail logs for this service:

```bash
docker-compose -f logs opbeans-load-generator
```
