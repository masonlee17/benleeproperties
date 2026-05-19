#!/bin/sh
set -e
exec gunicorn admin:app --bind "0.0.0.0:${PORT:-8080}" --workers 2 --timeout 120
