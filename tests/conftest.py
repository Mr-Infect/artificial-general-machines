import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.db import Database  # noqa: E402
from core.registry import CapabilityRegistry  # noqa: E402


@pytest.fixture
def registry():
    return CapabilityRegistry.load()


@pytest.fixture
def tmp_db(tmp_path):
    return Database(tmp_path / "test.sqlite")


@pytest.fixture
def results_root(tmp_path):
    return tmp_path / "results"


def docker_available():
    from runtime.executor import DockerExecutor
    return os.environ.get("AGM_TEST_DOCKER", "1") == "1" and DockerExecutor.available()
