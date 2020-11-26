# -*- coding: utf-8 -*-
import subprocess

from app.api import bp
from app import socketio

from flask import request


DEBUG = True


@bp.route('/list', methods=['GET'])
def get_list():
    return JOB_STATUS


@bp.route('/start', methods=['GET'])
def start_job():
    job = request.args.get('job')
    if DEBUG:
        cmd = ['sleep', '10']
    else:
        cmd = ['honcho', 'start', job]
    JOB_STATUS[job]['running'] = True
    socketio.emit('service_state', {'data': {job: 'start'}})

    # “I may not have gone where I intended to go, but I think I have ended up
    # where I needed to be.”
    # ― Douglas Adams, The Long Dark Tea-Time of the Soul
    p = subprocess.Popen(cmd)

    JOB_MANAGER[job] = p
    JOB_STATUS[job]['running'] = False
    socketio.emit('service_state', {'data': {job: 'stop'}})
    return {}


@bp.route('/stop', methods=['GET'])
def stop_job():
    """
    Find the job and kill it with fire
    """
    job = request.args.get('job')
    socketio.emit('service_state', {'data': {job: 'stop'}})
    if job in JOB_MANAGER:
        p = JOB_MANAGER[job]
        p.kill()
    if job in JOB_STATUS:
        j = JOB_STATUS[job]
        j['running'] = False

    return {}


def fetch_configured_jobs():
    """
    Parse the Procfile and determine which jobs are configured
    """
    ret = {}
    with open("../Procfile", "r") as fh_:
        p = fh_.readlines()
    for line in p:
        pname, url, name, _ = line.split(maxsplit=3)
        _, url = url.split('=')
        _, name = name.split('=')
        ret[pname[:-1]] = {
            'url': url,
            'name': name,
            'running': False,
            'p': None
            }
    return ret


# Simple structures for tracking status which is
# Thread-Safe-Enough (tm) for our needs because we
# limit ourselves to a single webserver proc and this
# is a private server
JOB_STATUS = fetch_configured_jobs()
JOB_MANAGER = {}
