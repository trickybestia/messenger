#!/usr/bin/env bash

set -euo pipefail

source ./venv/bin/activate

for arg in "$@"
do
  isort "$arg"
  black "$arg"
done
