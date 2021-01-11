#!/usr/bin/env sh

rm -rf Procfile
python3 generate_procfile.py "$OPBEANS_URLS" "$OPBEANS_RPMS" "$OPBEANS_RLS" > Procfile

if [ -z ${WS+x}  ];
then
    echo "Starting load tests..."
    exec "$@"
else
    echo "Starting webserver..."
    cd dyno
    # TODO This should eventually be replaced with a proper application packaging strategy
    # but it works for the time being.
    export PYTHONPATH=$PYTHONPATH:/app
    gunicorn -b 0.0.0.0 --worker-class eventlet -w 1 app:app
fi
