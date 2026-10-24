#!/usr/bin/env bash
set -euo pipefail

# This repository is already scaffolded. Use this script to recreate the main
# top-level learning directories in a fresh clone if needed.
mkdir -p \
  01-quantitative-aptitude/topics \
  02-data-interpretation/topics \
  03-logical-reasoning/topics \
  04-verbal-ability/topics \
  05-tcs-ninja-mock-tests \
  06-tcs-digital-mock-tests \
  templates daily-logs docs

echo "Aptitude learning directory scaffold is ready."
