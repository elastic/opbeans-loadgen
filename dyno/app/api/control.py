# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import signal

from pathlib import Path

from . import bp
import socketio
from flask import request, abort

DEBUG = os.environ.get('DYNO_DEBUG')


@bp.route('/list', methods=['GET'])
def get_list():
    """
    Return the current status of all configured
    jobs

    Returns
    -------
    dict
        The current job status dictionary.
        HTTP clients will receive the return as JSON.
    """
    return JOB_STATUS


@bp.route('/scenarios', methods=['GET'])
def get_scenarios():
    """
    Fetch a list of scenarios

    Returns
    -------
    dict
        A dictionary containing a list of scenarios under the `scenarios` key.
        HTTP clients will receive the return as JSON.
    """
    cur_dir = os.path.dirname(os.path.realpath(__file__)) 
    scenario_dir = os.path.join(cur_dir, "../../../scenarios")

    files = os.listdir(scenario_dir)

    ret = {'scenarios': []}

    for file in files:
        base_name = Path(file).stem
        ret['scenarios'].append(base_name)
    return ret


def _construct_toxi_env(
        job,
        port,
        scenario,
        error_weight,
        label_weight=None,
        label_name=None
        ):
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
       The name of the job. Should be passed without including the `opbeans-` prefix.

    port : str
        The port for the environment. Can also be passed as a int type.

    scenario : str
        Thie scenario for use with this instance. Should be passed as simply
        the name and NOT as a filename.

    error_weight : int
        The relative "weight" of errors. Higher number result in the load generator
        choosing to hit pages known to produce errors a higher percentage of the time.
        This number is entirely arbitrary and is only relative to statically configured
        weights in the scenario file itself.

    label_weight : int
        In the case of the `dyno` scenario, a label_weight parameter can be passed which
        increases the rate at which a given label is accessed. The label weight is controlled
        via the `label_name` parameter. Does NOT work with scenarios other than `dyno`!

    label_name : str
        Used in conjunction with `label_weight` to specify a label which should be hit at a higher
        or lower rate, which is controlled by the `label_weight` parameters.

    
    Returns
    -------
    dict
        Dictionary containing the environment keys and values
   
    Examples
    --------
    Sample call showing just the required parameters

    >>> _construct_toxi_env('python', 9999, 'my_great-scenario', 99)
    {'OPBEANS_BASE_URL': 'http://toxi:9999', 'OPBEANS_NAME': 'opbeans-python', 'ERROR_WEIGHT': '99'}

    """
    toxi_env = os.environ.copy()
    toxi_env['OPBEANS_BASE_URL'] = "http://toxi:{}".format(port)
    toxi_env['OPBEANS_NAME'] = "opbeans-" + job
    toxi_env['ERROR_WEIGHT'] = str(error_weight)

    if scenario == 'dyno':
        toxi_env['LABEL_WEIGHT'] = str(label_weight)
        toxi_env['LABEL_NAME'] = label_name
    return toxi_env


@bp.route('/update', methods=['POST'])
def update_job():
    """
    We try to reconstruct the existing job by querying
    the status dictionary and then we update as necessary.
    Then we kill the job and start it again with the new
    values.
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
                "error_weight": r.get('error_weight', "0")
                }
        return {}

    config = JOB_STATUS[job]

    if 'workers' in r:
        config['workers'] = r['workers']
    if 'error_weight' in r:
        config['error_weight'] = r['error_weight']
    if 'label_weight' in r:
        config['label_weight'] = r['label_weight']
    if 'label_name' in r:
        config['label_name'] = r['label_name']
    _stop_job(job)

    if DEBUG:
        print('Relaunching job: ', config)
    _launch_job(job, config)
    _update_status(job, config)
    return {}


def _update_status(job, config):
    if job not in JOB_STATUS:
        # TODO refactor to single source of truth
        JOB_STATUS[job] = {
                'duration': "31536000",
                'delay': "0.600",
                "scenario": "molotov_scenarios",
                "workers": "3",
                "error_weight": "0"
                }
    status = JOB_STATUS[job]
    status['running'] = True
    status['duration'] = config['duration']
    status['delay'] = config['delay']
    status['scenario'] = config['scenario']
    status['workers'] = config['workers']
    status['error_weight'] = config['error_weight']
    status['port'] = config['port']
    status['label_weight'] = config.get('label_weight')
    status['label_name'] = config.get('label_name')
    status['name'] = job


def _launch_job(job, config):
    # Cut the actual number of workers to 10% of the raw value or we just crush
    # the application
    if DEBUG:
        print('Job launch received: ',
                config['job'], config['port'],
                config['duration'],
                config['delay'],
                config['workers'],
                config['scenario'],
                config['error_weight'])

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

    toxi_env = _construct_toxi_env(job, config['port'], config['scenario'], config['error_weight'])

    _update_status(job, config) 

    # “I may not have gone where I intended to go, but I think I have ended up
    # where I needed to be.”
    # ― Douglas Adams, The Long Dark Tea-Time of the Soul
    p = subprocess.Popen(cmd, cwd="../", preexec_fn=os.setsid, env=toxi_env)
    JOB_MANAGER[job] = p


@bp.route('/start', methods=['POST'])
def start_job():
    r = request.get_json() or {}
    job = r.get('job')
    config = {
            'port': r.get('port'),
            'scenario': r.get('scenario', "molotov_scenarios"),
            'duration': r.get('duration', "31536000"),
            'delay': r.get('delay', "0.600"),
            'workers': r.get('workers', "3"),
            'error_weight': r.get('error_weight', "0"),
            'label_weight': r.get('label_weight', "2"),
            'label_name': r.get('label_name', 'foo_label')
            }

    job = job.replace('opbeans-', '')

    if config['scenario']:
        config['scenario'] = "scenarios/" + config['scenario'] + ".py"

    _launch_job(job, config)

    return {}


def _stop_job(job):
    s = socketio.Client()
    s.emit('service_state', {'data': {job: 'stop'}})
    if job in JOB_MANAGER:
        p = JOB_MANAGER[job]
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        JOB_MANAGER[job] = None
    if job in JOB_STATUS:
        j = JOB_STATUS[job]
        j['running'] = False


@bp.route('/stop', methods=['GET'])
def stop_job():
    """
    Find the job and kill it with fire
    """
    job = request.args.get('job')
    job = job.replace('opbeans-', '')
    _stop_job(job)
    return {}


# Simple structures for tracking status which is
# Thread-Safe-Enough (tm) for our needs because we
# limit ourselves to a single webserver proc and this
# is a private server
JOB_STATUS = {}
JOB_MANAGER = {}
