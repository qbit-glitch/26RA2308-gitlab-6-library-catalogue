#!/usr/bin/env bash
# Grades your submission:  bash tests/run_tests.sh   (extra options are passed to grade.py)
cd "$(dirname "$0")/.." || exit 2
exec python3 tests/grade.py "$@"
