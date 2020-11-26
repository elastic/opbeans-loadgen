#!/usr/bin/env sh

rm -rf Procfile
python3 generate_procfile.py "$OPBEANS_URLS" "$OPBEANS_RPMS" "$OPBEANS_RLS" > Procfile

if [ $WS ];
then
    echo "Starting webserver..."
    gunicorn -b 0.0.0.0 --worker-class eventlet -w 1 app:app
else
    echo "Starting load tests..."
    exec "$@"
fi
