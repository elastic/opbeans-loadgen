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


def _construct_toxi_env(job, port):
    toxi_env = os.environ.copy()
    toxi_env['OPBEANS_BASE_URL'] = "http://toxi:{}".format(port)
    toxi_env['OPBEANS_NAME'] = job
    return toxi_env


@bp.route('/start', methods=['GET'])
def start_job():
    job = request.args.get('job')
    port = request.args.get('port')
    scenario = request.args.get('scenario')
    duration = request.args.get('duration')
    delay = request.args.get('delay')

    job = job.replace('opbeans-', '')

    defaults = {
        "duration": "31536000",
        "delay": "0.600",
        "scenario": "molotov_scenarios.py"
    }
    toxi_env = _construct_toxi_env(job, port)

    if DEBUG:
        cmd = ['sleep', '10']
    else:
        cmd = [
            "/app/venv/bin/python",
            "/app/venv/bin/molotov",
            "-v",
            "--duration",
            duration or defaults["duration"],
            "--delay",
            delay or defaults["delay"],
            "--uvloop",
            "--statsd",
            "--statsd-address",
            "udp://stats-d:8125",
            scenario or defaults["scenario"]
            ]
    JOB_STATUS[job]['running'] = True
    s = socketio.Client()
    s.emit('service_state', {'data': {job: 'start'}})

    # “I may not have gone where I intended to go, but I think I have ended up
    # where I needed to be.”
    # ― Douglas Adams, The Long Dark Tea-Time of the Soul
    p = subprocess.Popen(cmd, cwd="../", preexec_fn=os.setsid, env=toxi_env)
    JOB_MANAGER[job] = p
    return {}


@bp.route('/stop', methods=['GET'])
def stop_job():
    """
    Find the job and kill it with fire
    """
    job = request.args.get('job')
    job = job.replace('opbeans-', '')
    s = socketio.Client()
    s.emit('service_state', {'data': {job: 'stop'}})
    if job in JOB_MANAGER:
        p = JOB_MANAGER[job]
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        JOB_MANAGER[job] = None
    if job in JOB_STATUS:
        j = JOB_STATUS[job]
        j['running'] = False

    return {}


def fetch_configured_jobs():
    """
    Parse the Procfile and determine which jobs are configured
    """
    ret = {}
    cur_dir = os.path.dirname(os.path.realpath(__file__)) 
    procfile_path = os.path.join(cur_dir, "../../../Procfile")
    with open(procfile_path, "r") as fh_:
        p = fh_.readlines()
    for line in p:
        try:
            pname, url, name, _ = line.split(maxsplit=3)
            _, url = url.split('=')
            _, name = name.split('=')
            ret[pname[:-1]] = {
                'url': url,
                'name': name,
                'running': False,
                'p': None
                }
        except ValueError:
            continue
    return ret


# Simple structures for tracking status which is
# Thread-Safe-Enough (tm) for our needs because we
# limit ourselves to a single webserver proc and this
# is a private server
try:
    JOB_STATUS = fetch_configured_jobs()
except FileNotFoundError:
    JOB_STATUS = {}
JOB_MANAGER = {}
