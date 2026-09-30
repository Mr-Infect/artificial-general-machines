#!/usr/bin/env bash
# Run the first research benchmark end to end and produce the suite report.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m experiments.run experiments/manifests/cross_domain_transfer_001.yaml "$@"
python3 -m experiments.report --suite cross_domain_001
