#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
for sensor_python in .venv/bin/python python3.12 python3.11 python3; do
 if command -v "$sensor_python" >/dev/null 2>&1 && "$sensor_python" -c 'import sys; assert sys.version_info[:2] in [(3,11),(3,12)]' >/dev/null 2>&1; then
  exec "$sensor_python" launcher.py
 fi
done
printf '%s\n' 'Install Python 3.11 or 3.12 with venv support, then run this script again.' >&2
exit 1
