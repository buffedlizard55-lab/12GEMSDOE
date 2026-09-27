#!/usr/bin/env bash
set -euo pipefail
python "$(dirname "$0")/download_competition_data.py"
