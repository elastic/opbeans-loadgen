import sys


def create_procfile(service_env_string, rpm_env_string='',rls_env_string='', num_workers="", num_of_ips="", ip_header="HTTP_X_FORWARDED_FOR", *args):
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
        service_name, service_url = service.split(':', maxsplit=1)
        process_name = service_name.split('-', maxsplit=1)[1].replace(
            '-', ''
        )  # we use second part of name and strip all remaining dashes
        delay = 60.0 / rpms.get(service_name, 100)
        run_length = rls.get(service_name, 365 * 24 * 60 * 60)
        sys.stdout.write(
            '{0}: OPBEANS_BASE_URL={1} OPBEANS_NAME={2} NUM_OF_IPS={6} REAL_IP_HEADER={7} molotov -v --duration {3} --delay {4:.3f} --workers {5} --uvloop molotov_scenarios.py\n'.format(
                process_name,
                service_url,
                service_name,
                run_length,
                delay,
                1 if num_workers == "" else int(num_workers),
                100 if num_of_ips == "" else int(num_of_ips),
                "HTTP_X_FORWARDED_FOR" if ip_header == "" else ip_header,
            )
        )
    sys.stdout.flush()


if __name__ == '__main__':
    create_procfile(*sys.argv[1:])