#!/usr/bin/env bash

rm -rf Procfile
python3 generate_procfile.py "$OPBEANS_URLS" "$OPBEANS_RPMS" "$OPBEANS_RLS" "$NUM_OF_WORKERS" "$NUM_OF_IPS" "$REAL_IP_HEADER"  > Procfile

exec "$@"