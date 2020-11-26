#!/usr/bin/env sh

rm -rf Procfile
python3 generate_procfile.py "$OPBEANS_URLS" "$OPBEANS_RPMS" "$OPBEANS_RLS" > Procfile

if [ $WS ];
then
    echo "Starting webserver..."
    gunicorn -b 0.0.0.0 app:app --capture-output  -t 90 -w 8
else
    echo "Starting load tests..."
    exec "$@"
fi
