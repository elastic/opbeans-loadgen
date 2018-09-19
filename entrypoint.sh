#!/usr/bin/env bash

rm -rf Procfile
python3 generate_procfile.py "$OPBEANS_URLS" "$OPBEANS_RPMS" "$OPBEANS_RLS" "$NUM_WOKERS" "$REAL_IP_HEADER" "$NUM_OF_IPS" > Procfile

exec "$@"