#!/usr/bin/env bash
# Build (or rebuild) the sandbox image. The tag is derived from the runner's content hash,
# so the experiment runner will build it on demand too; this script just does it up front.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -c "from runtime.executor import DockerExecutor as D; d=D(); print('image', d.image, d.ensure_image())"
