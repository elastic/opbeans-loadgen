import os
import sys


def create_procfile(service_env_string, rpm_env_string='',rls_env_string='', *args):
    if os.environ.get('WS'):
        cmd = '{0}: OPBEANS_BASE_URL={1} OPBEANS_NAME={2} molotov -v --duration {3} --delay {4:.3f} --uvloop --statsd --statsd-address udp://stats-d:8125 molotov_scenarios.py\n'
    else:
        cmd = '{0}: OPBEANS_BASE_URL={1} OPBEANS_NAME={2} molotov -v --duration {3} --delay {4:.3f} --uvloop molotov_scenarios.py\n'
    services = service_env_string.split(',')
    if rpm_env_string:
        rpms = {
            service_name: int(rpm) for service_name, rpm in (entry.split(':') for entry in rpm_env_string.split(','))
        }
    else:
        rpms = {}

    if rls_env_string:
        rls = {
            service_name: int(rl) for service_name, rl in (entry.split(':') for entry in rls_env_string.split(','))
        }
    else:
        rls = {}

    for service in services:
        try:
            service_name, service_url = service.split(':', 1)
        except ValueError:
            print('ERROR: Must supply service(s) in the form service_name:service_url')
            sys.exit(1)
        process_name = service_name.split('-', 1)[1].replace(
            '-', ''
        )  # we use second part of name and strip all remaining dashes
        delay = 60.0 / rpms.get(service_name, 100)
        run_length = rls.get(service_name, 365 * 24 * 60 * 60)
        sys.stdout.write(
            cmd.format(
                process_name,
                service_url,
                service_name,
                run_length,
                delay,
            )
        )
    sys.stdout.flush()


if __name__ == '__main__':
    create_procfile(*sys.argv[1:])
