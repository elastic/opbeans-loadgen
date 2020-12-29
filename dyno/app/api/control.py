# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import signal

from pathlib import Path

from . import bp
import socketio
from flask import request

DEBUG = os.environ.get('DYNO_DEBUG')


@bp.route('/list', methods=['GET'])
def get_list():
    return JOB_STATUS


@bp.route('/scenarios', methods=['GET'])
def get_scenarios():
    """
    Fetch a list of scenarios
    """
    ret = {'scenarios': []}
    cur_dir = os.path.dirname(os.path.realpath(__file__)) 
    scenario_dir = os.path.join(cur_dir, "../../../scenarios")

    files = os.listdir(scenario_dir)
    for file in files:
        base_name = Path(file).stem
        ret['scenarios'].append(base_name)
    return ret


def _construct_toxi_env(job, port, scenario, error_weight, label_weight=None, label_name=None):
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
    # workers = r.get('workers', "50")
    # error_weight = r.get('error_weight', "0")

    if job is None:
        print('No job to update')
        # TODO better error return
        return {}

    if job not in JOB_STATUS:
        # TODO refactor to single source of truth
        JOB_STATUS[job] = {'duration': "31536000", 'delay': "0.600", "scenario": "molotov_scenarios", "workers": r.get('workers', "3"), "error_weight": r.get('error_weight', "0")}
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
    print('Relaunching job: ', config)
    _launch_job(job, config['port'], config['duration'], config['delay'], config['workers'], config['scenario'], config['error_weight'], config['label_weight'], config['label_name'])
    _update_status(job, config['port'], config['duration'], config['delay'], config['workers'], config['scenario'], config['error_weight'], config['label_weight'], config['label_name'])
    return {}


def _update_status(job, port, duration, delay, workers, scenario, error_weight, label_weight, label_name):
    if job not in JOB_STATUS:
        # TODO refactor to single source of truth
        JOB_STATUS[job] = {'duration': "31536000", 'delay': "0.600", "scenario": "molotov_scenarios", "workers": "3", "error_weight": "0"}
    status = JOB_STATUS[job]
    status['running'] = True
    status['duration'] = duration
    status['delay'] = delay
    status['scenario'] = scenario
    status['workers'] = workers
    status['error_weight'] = error_weight
    status['port'] = port
    status['label_weight'] = label_weight
    status['label_name'] = label_name
    status['name'] = job


def _launch_job(job, port, duration, delay, workers, scenario, error_weight, label_weight=None, label_name=None):
    # Cut the actual number of workers to 10% of the raw value or we just crush
    # the application
    print('Job launch received: ', job, port, duration, delay, workers, scenario, error_weight)

    if DEBUG:
        cmd = ['sleep', '10']
    else:
        cmd = [
            "/app/venv/bin/python",
            "/app/venv/bin/molotov",
            "-v",
            "--duration",
            str(duration),
            "--delay",
            str(delay),
            "--uvloop",
            "--workers",
            str(int(workers)),
            "--statsd",
            "--statsd-address",
            "udp://stats-d:8125",
            scenario
            ]
#<<<<<<< HEAD
#    JOB_STATUS[job]['running'] = True
    s = socketio.Client()
    s.emit('service_state', {'data': {job: 'start'}})
#=======
    print('Launching with: ', cmd)
#    socketio.emit('service_state', {'data': {job: 'start'}})
#>>>>>>> 4e765c5b9ef2ec57b6dc9fe5678d655c9ac9662d

    toxi_env = _construct_toxi_env(job, port, scenario, error_weight)

    _update_status(job, port, duration, delay, workers, scenario, error_weight, label_weight, label_name)

    # “I may not have gone where I intended to go, but I think I have ended up
    # where I needed to be.”
    # ― Douglas Adams, The Long Dark Tea-Time of the Soul
    p = subprocess.Popen(cmd, cwd="../", preexec_fn=os.setsid, env=toxi_env)
    JOB_MANAGER[job] = p


@bp.route('/start', methods=['POST'])
def start_job():
    r = request.get_json() or {}
    job = r.get('job')
    port = r.get('port')
    scenario = r.get('scenario', "molotov_scenarios")
    duration = r.get('duration', "31536000")
    delay = r.get('delay', "0.600")
    workers = r.get('workers', "3")
    error_weight = r.get('error_weight', "0")

    label_weight = r.get('label_weight', "2")
    label_name = r.get('label_name', 'foo_label')

    job = job.replace('opbeans-', '')
#<<<<<<< HEAD
#    s = socketio.Client()
#    s.emit('service_state', {'data': {job: 'stop'}})
#=======

    if scenario:
        scenario = "scenarios/" + scenario + ".py"

    _launch_job(job, port, duration, delay, workers, scenario, error_weight, label_weight, label_name)

    return {}


def _stop_job(job):
#    socketio.emit('service_state', {'data': {job: 'stop'}})
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
try:
    JOB_STATUS = fetch_configured_jobs()
except FileNotFoundError:
    JOB_STATUS = {}
JOB_MANAGER = {}
