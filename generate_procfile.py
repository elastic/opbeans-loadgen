import sys


def create_procfile(service_env_string, rpm_env_string='', *args):
    services = service_env_string.split(',')
    rpms = {service_name: int(rpm) for service_name, rpm in (entry.split(':') for entry in rpm_env_string.split(','))}
    for service in services:
        service_name, service_url = service.split(':', maxsplit=1)
        process_name = service_name.split('-', maxsplit=1)[1].replace(
            '-', ''
        )  # we use second part of name and strip all remaining dashes
        delay = 60.0 / rpms.get(service_name, 100)
        sys.stdout.write(
            '{0}: OPBEANS_BASE_URL={1} OPBEANS_NAME={2} molotov -v --duration {3} --delay {4:.3f} --uvloop molotov_scenarios.py\n'.format(
                process_name,
                service_url,
                service_name,
                365 * 24 * 60 * 60,
                delay,
            )
        )
    sys.stdout.flush()


if __name__ == '__main__':
    create_procfile(*sys.argv[1:])

