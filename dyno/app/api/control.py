# -*- coding: utf-8 -*-
import os
import subprocess
import signal

from pathlib import Path

from . import bp
import socketio
from flask import request

# TODO Pull this from config object instead
DEBUG = os.environ.get('DYNO_DEBUG')

""" Public HTTP methods """


@bp.route('/start', methods=['POST'])
def start_job() -> dict:
    """
    Start a load-generation job

    Exposed via HTTP at /api/start

    Supported HTTP methods: GET

    Note
    ----
    Paramaters are received via JSON in a Flask request object. They
    may not be passed directly to this function.

    Parameters
    ----------
    port : str
        The port number to target

    scenario : str
        The scenario to launch. Defaults to `molotov_scenarios`

    duration : str
        The duration for the test to run in seconds. Default is 365 *days*.

    delay : str
        The average delay between requests. See the Molotov documation
        for more information on this option.

        https://molotov.readthedocs.io/en/stable/cli/?highlight=delay#command-line-options

    workers : str
        The number of workers to start. See the Molotov documentation
        for more details on this option:

        https://molotov.readthedocs.io/en/stable/cli/?highlight=workers#command-line-options

    error_weight : str
        The relative "weight" of errors. Higher number result in the load
        generator choosing to hit pages known to produce errors a higher
        percentage of the time.

        This number is entirely arbitrary and is only relative to statically
        configured weights in the scenario file itself.

    app_latency_weight : str
        In the case of the `dyno` scenario, an app_latency_weight
        parameter can be passed which increases the rate at which a given
        label is accessed.

        Does NOT work with scenarios other than `dyno`!

    app_latency_label : str
        Used in conjunction with `app_latency_weightr` to specify a
        label which should be hit at a higher or lower rate.

    app_latency_lower_bound : int
        The lower bound of latency which should be applied to requests which
        hit the delayed endpoint

    app_latency_upper_bound : int
        The upper bound of latency which should be applied to requests which
        hit the delayed endpoint

    Examples
    --------
    Sample JSON payload to send to this endpoint:
    > {"job":"opbeans-python","port":"8000"}
    """
    r = request.get_json() or {}
    job = r.get('job')
    config = {
            'port': r.get('port'),
            'scenario': r.get('scenario', "molotov_scenarios"),
            'duration': r.get('duration', "31536000"),
            'delay': r.get('delay', "0.600"),
            'workers': r.get('workers', "3"),
            'error_weight': r.get('error_weight', "0"),
            'app_latency_weight': r.get('app_latency_weight', "0"),
            'app_latency_label': r.get('app_latency_label', 'dyno_latency'), # noqa
            'app_latency_lower_bound': r.get('app_latency_lower_bound', 1),  # noqa
            'app_latency_upper_bound': r.get('app_latency_upper_bound', 1000),  # noqa
            }

    job = job.replace('opbeans-', '')

    if config['scenario']:
        config['scenario'] = "scenarios/" + config['scenario'] + ".py"

    _launch_job(job, config)

    return {}


@bp.route('/list', methods=['GET'])
def get_list() -> dict:
    """
    Return the current status of all configured
    jobs

    Exposed via HTTP at /api/list

    Supported HTTP methods: GET

    Returns
    -------
    dict
        The current job status dictionary.
        HTTP clients will receive the return as JSON.

    Examples
    --------
    ❯ curl -s http://localhost:8999/api/list|jq
    {
      "python": {
        "delay": "0.600",
        "duration": "31536000",
        "error_weight": "0",
        "app_latency_label": "dyno_delay",
        "app_latency_weight": "2",
        "app_latency_lower_bound": "1",
        "app_latency_upper_bound": "1000",
        "name": "python",
        "port": "8000",
        "running": false,
        "scenario": "scenarios/molotov_scenarios.py",
        "workers": "3"
      }
    }
    """
    return JOB_STATUS


@bp.route('/update', methods=['POST'])
def update_job() -> dict:
    """
    Updates a job with a new configuration.

    We try to reconstruct the existing job by querying
    the status dictionary and then we update as necessary.
    Then we kill the job and start it again with the new
    values.

    Exposed via HTTP at /api/update

    Supported HTTP methods: POST

    Parameters
    ----------
    job : str
        The name of the job to modify. (Required)

    workers : str
        The number of workers the load generator should use. (Optional)

    error_weight : str
        The relative "weight" of errors. Higher number result in the load
        generator choosing to hit pages known to produce errors a higher
        percentage of the time.

        This number is entirely arbitrary and is only relative to statically
        configured weights in the scenario file itself. (Optional)

    app_latency_weight : str
        In the case of the `dyno` scenario, an `app_latency_weight`
        parameter can be passed which increases the rate at which a given
        label is accessed.

        Does NOT work with scenarios other than `dyno`! (Optional)

    app_latency_label : str
        Used in conjunction with `app_latency_eight` to specify a label which
        should be hit at a higher or lower rate, which is controlled by
        the `app_latency_weight` parameter.

    app_latency_lower_bound : int
        The lower bound of latency which should be applied to requests which
        hit the delayed endpoint

    app_latency_upper_bound : int
        The upper bound of latency which should be applied to requests which
        hit the delayed endpoint

    Returns
    -------
    An empty dictionary on success

    Examples
    --------
    Sample JSON payload to send to this endpoint:
    > {"job":"python","workers":2.1}

    Note
    ----
    Paramaters are received via JSON in a Flask request object. They
    may not be passed directly to this function.
    """
    r = request.get_json() or {}
    job = r.get('job')

    if job is None:
        return "Must supply job", 400
    if job not in JOB_STATUS:
        # TODO refactor to single source of truth
        JOB_STATUS[job] = {
                'duration': "31536000",
                'delay': "0.600",
                "scenario": "molotov_scenarios",
                "workers": r.get('workers', "3"),
                "error_weight": r.get('error_weight', "0"),
                "app_latency_weight": r.get('app_latency_weight', 0),
                "app_latency_label": r.get("app_latency_label", "dyno_app_latency"),  # noqa
                "app_latency_lower_bound": r.get("app_latency_lower_bound", 1),
                "app_latency_upper_bound": r.get("app_latency_upper_bound", 1000)  # noqa
                }
        return {}

    config = JOB_STATUS[job]

    if 'workers' in r:
        config['workers'] = r['workers']
    if 'error_weight' in r:
        config['error_weight'] = r['error_weight']
    if 'app_latency_weight' in r:
        config['app_latency_weight'] = r['app_latency_weight']
    if 'app_latency_label' in r:
        config['app_latency_label'] = r['app_latency_label']
    if 'app_latency_lower_bound' in r:
        config['app_latency_lower_bound'] = r['app_latency_lower_bound']
    if 'app_latency_upper_bound' in r:
        config['app_latency_upper_bound'] = r['app_latency_upper_bound']
    _stop_job(job)

    if DEBUG:
        print('Relaunching job: ', config)
    _launch_job(job, config)
    _update_status(job, config)
    return {}


@bp.route('/stop', methods=['GET'])
def stop_job() -> dict:
    """
    Stop a load-generation job

    Exposed via HTTP at /api/stop

    Supported HTTP methods: POST

    Note
    ----
    Paramaters are received query arguments in a Flask request object. They
    may not be passed directly to this function.

    Parameters
    ----------
    job : str
        The job to stop

    Examples
    --------
    > curl http://localhost:8999/api/stop?job=opbeans-python
    """
    job = request.args.get('job')
    job = job.replace('opbeans-', '')
    _stop_job(job)
    return {}


@bp.route('/splays', methods=['GET'])
def get_splays() -> dict:
    """
    Fetch a list of splays

    Exposed via HTTP at /api/splays
    Supported HTTP methods: GET

    Returns
    -------
    dict
        A dictionary containing a list of possible splay. A splay
        is a property across which delayed requests are distributed.

    Examples
    --------
    ❯ curl -s http://localhost:8999/api/splays|jq
    {
        "splays": [
            "User-agent: Safari",
            "IP addresses: 10.0.0.0/8"
        ]
    }
    """
    # Fixed for the time being
    ret = {'splays': ['User-Agent: Safari']}
    return ret


@bp.route('/scenarios', methods=['GET'])
def get_scenarios() -> dict:
    """
    Fetch a list of scenarios.

    Exposed via HTTP at /api/scenarios
    Supported HTTP methods: GET

    Returns
    -------
    dict
        A dictionary containing a list of scenarios under the `scenarios` key.
        HTTP clients will receive the return as JSON.

    Note
    ----
    To add a new scenario to the application, it must be added to the
    scenarios/ folder before it appears in this list.

    Examples
    --------
    ❯ curl -s http://localhost:8999/api/scenarios|jq
    {
        "scenarios": [
            "dyno",
            "molotov_scenarios",
            "high_error_rates"
        ]
    }
    """
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    scenario_dir = os.path.join(cur_dir, "../../../scenarios")

    files = os.listdir(scenario_dir)

    ret = {'scenarios': []}

    for file in files:
        if file.startswith('__'):
            continue
        base_name = Path(file).stem
        ret['scenarios'].append(base_name)
    return ret


""" Private helper functions """


def _construct_toxi_env(
        job: str,
        port: str,
        scenario: str,
        error_weight: int,
        app_latency_weight=None,
        app_latency_label=None,
        app_latency_lower_bound=None,
        app_latency_upper_bound=None,

        ) -> dict:
    """
    Construct a dictionary representing an Opbeans environment
    which is fronted by a Toxiproxy instance.

    Note
    ----
    The `label_weight` and `label_name` parameters are currently used
    only in the context of the `dyno` scenario. Otherwise, they are
    ignored.

    Parameters
    ----------
    job : str
       The name of the job. Should be passed without including the `opbeans-`
       prefix.

    port : str
        The port for the environment. Can also be passed as a int type.

    scenario : str
        Thie scenario for use with this instance. Should be passed as simply
        the name and NOT as a filename.

    error_weight : int
        The relative "weight" of errors. Higher number result in the load
        generator choosing to hit pages known to produce errors a higher
        percentage of the time.

        This number is entirely arbitrary and is only relative to statically
        configured weights in the scenario file itself.

    app_latency_weight : int
        In the case of the `dyno` scenario, the app_latency_weight parameter
        can be passed which increases the rate at which an endpoint which
        artifically introduces latency is hit.

    app_latency_label : str
        Used in conjunction with `app_latency_weight` to specify a label which
        should be applied to latent requests.

    app_latency_lower_bound : int
        Used in conjunction with `app_latency_weight`, this parameter
        specifies the lower bound for latency. Requests will never be
        less latent than this value.

    app_latency_upper_bound : str
        Used in conjunction with `app_latency_weight`, this parameter
        specifies the upper bound for latency. Requests will never by (much)
        more latent than this value.

    app_latency_user_agent : str
        Used in conjunction with `app_latency_weight`, this parameter
        specifies a user agent for the latent requests.

    Returns
    -------
    dict
        Dictionary containing the environment keys and values

    Examples
    --------
    Sample call showing just the required parameters

    >>> _construct_toxi_env('python', 9999, 'my_great-scenario', 99)
    {
        'OPBEANS_BASE_URL': 'http://toxi:9999',
        'OPBEANS_NAME': 'opbeans-python',
        'ERROR_WEIGHT': '99'
    }

    """
    toxi_env = os.environ.copy()
    toxi_env['OPBEANS_BASE_URL'] = "http://toxi:{}".format(port)
    toxi_env['OPBEANS_NAME'] = "opbeans-" + job
    toxi_env['ERROR_WEIGHT'] = str(error_weight)
    if app_latency_weight:
        toxi_env['APP_LATENCY_WEIGHT'] = str(app_latency_weight)
    if app_latency_label:
        toxi_env['APP_LATENCY_LABEL'] = app_latency_label
    if app_latency_lower_bound:
        toxi_env['APP_LATENCY_LOWER_BOUND'] = str(app_latency_lower_bound)
    if app_latency_upper_bound:
        toxi_env['APP_LATENCY_UPPER_BOUND'] = str(app_latency_upper_bound)
    return toxi_env


def _update_status(job: str, config: dict) -> None:
    """
    Helper function for updating the status of a job

    This function can only be called directly and is
    not accessible via HTTP.

    Parameters
    ----------
    job : str
        The name of the job to update

    config : dict
        A configuration dictionary containing a valid
        configuration for the job.

    Returns
    -------
    None

    Note
    ----
    See implementation for a list of required keys in the
    configuration dictionary.

    Examples
    --------
    >>> config = {'duration': '90', 'delay': '91', \
            'scenario': 'dyno', 'workers': '92',\
            'error_weight': '93', 'port': '95', \
            'app_latency_weight': '96','app_latency_label': 'my_label', \
            'app_latency_lower_bound': 1,'app_latency_upper_bound': 1000}
    >>> update_status('python', config)
    """
    if job not in JOB_STATUS:
        # TODO refactor to single source of truth
        JOB_STATUS[job] = {
                'duration': "31536000",
                'delay': "0.600",
                "scenario": "molotov_scenarios",
                "workers": "3",
                "error_weight": "0",
                "app_latency_weight": "0",
                "app_latency_label": "dyno_app_latency",
                "app_latency_lower_bound": "1",
                "app_latency_upper_bound": "1000"
                }
    status = JOB_STATUS[job]
    status['running'] = True
    status['duration'] = config['duration']
    status['delay'] = config['delay']
    status['scenario'] = config['scenario']
    status['workers'] = config['workers']
    status['error_weight'] = config['error_weight']
    status['port'] = config['port']
    status['app_latency_weight'] = config.get('app_latency_weight')
    status['app_latency_label'] = config.get('app_latency_label')
    status['app_latency_lower_bound'] = config.get('app_latency_lower_bound')
    status['app_latency_upper_bound'] = config.get('app_latency_upper_bound')
    status['name'] = job


def _launch_job(job: str, config: dict) -> None:
    """
    Spawn a new load-generation job

    This function can only be called directly and is
    not accessible via HTTP.

    Parameters
    ----------
    job : str

    config : dict
        A configuration dictionary containing a valid configuration
        for the job.

    Returns
    -------
    None

    Examples
    --------
    >>> config = {'duration': '90', 'delay': '91', \
            'scenario': 'dyno', 'workers': '92',\
            'error_weight': '93', 'port': '95'}
    >>> update_status('python', config)
    """
    if DEBUG:
        print(
            'Job launch received: ', config
        )

    if DEBUG:
        cmd = ['sleep', '10']
    else:
        cmd = [
            "/app/venv/bin/python",
            "/app/venv/bin/molotov",
            "-v",
            "--duration",
            str(config['duration']),
            "--delay",
            str(config['delay']),
            "--uvloop",
            "--workers",
            str(int(config['workers'])),
            "--statsd",
            "--statsd-address",
            "udp://stats-d:8125",
            config['scenario']
            ]
    s = socketio.Client()
    s.emit('service_state', {'data': {job: 'start'}})
    if DEBUG:
        print('Launching with: ', cmd)

    toxi_env = _construct_toxi_env(
            job,
            config['port'],
            config['scenario'],
            config['error_weight'],
            # TODO These are optional so that we don't
            # break backward compatability with older clients.
            # Eventually the lookup fallbacks can be removed.
            config.get('app_latency_weight'),
            config.get('app_latency_label'),
            config.get('app_latency_lower_bound'),
            config.get('app_latency_upper_bound'),
            )

    _update_status(job, config)

    # “I may not have gone where I intended to go, but I think I have ended up
    # where I needed to be.”
    # ― Douglas Adams, The Long Dark Tea-Time of the Soul
    p = subprocess.Popen(cmd, cwd="../", preexec_fn=os.setsid, env=toxi_env)
    JOB_MANAGER[job] = p


def _stop_job(job: str) -> None:
    """
    Helper function for stopping a job

    Note
    ----
    This function can only be called directly and is
    not accessible via HTTP.

    Parameters
    ----------
    job : str
        The job to stop

    Returns
    -------
    None

    Examples
    --------
    >>> _stop_job('opbeans-python')


    """
    s = socketio.Client()
    s.emit('service_state', {'data': {job: 'stop'}})
    if job in JOB_MANAGER:
        p = JOB_MANAGER[job]
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        JOB_MANAGER[job] = None
    if job in JOB_STATUS:
        j = JOB_STATUS[job]
        j['running'] = False


# Simple structures for tracking status which is
# Thread-Safe-Enough (tm) for our needs because we
# limit ourselves to a single webserver proc and this
# is a private server
JOB_STATUS = {}
JOB_MANAGER = {}
