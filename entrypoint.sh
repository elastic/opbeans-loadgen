#!/usr/bin/env sh

rm -rf Procfile
python3 generate_procfile.py "$OPBEANS_URLS" "$OPBEANS_RPMS" "$OPBEANS_RLS" > Procfile

exec "$@"
