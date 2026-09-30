"""Sandbox executors (Section 7).

DockerExecutor is the real sandbox: CPU and memory limits, timeout, no
privileges, no host filesystem, no Docker socket, no network. Input goes in
over stdin and output comes back over stdout, so nothing is mounted.

ProcessExecutor runs the same runner as a local subprocess. It measures the
same quantities but only enforces the timeout; memory limits are checked
after the fact. It exists for unit tests and for hosts without Docker, and
every experiment records which executor was used.
"""
from __future__ import annotations

import hashlib
import json
import os
import resource
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from core.models import SandboxResult

ROOT = Path(__file__).resolve().parent.parent
SANDBOX_DIR = ROOT / "sandbox"
RUNNER = SANDBOX_DIR / "runner.py"


def _parse_output(stdout: str) -> Optional[Dict[str, Any]]:
    stdout = stdout.strip()
    if not stdout:
        return None
    try:
        return json.loads(stdout[stdout.rfind("\n{") + 1:] if "\n{" in stdout else stdout)
    except json.JSONDecodeError:
        return None


class ProcessExecutor:
    name = "process"

    def run(self, payload: Dict[str, Any], limits: Dict[str, Any]) -> SandboxResult:
        timeout = float(limits.get("timeout_s", 30))
        mem_limit = float(limits.get("memory_mb", 512))

        def _pre():
            cpu = int(timeout) + 2
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))

        t0 = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run([sys.executable, str(RUNNER)], input=json.dumps(payload), capture_output=True,
                                  text=True, timeout=timeout, preexec_fn=_pre, cwd=str(SANDBOX_DIR))
            stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as e:
            stdout = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            code, timed_out = -9, True
        runtime = time.monotonic() - t0
        artifact = _parse_output(stdout)
        cpu_time = float(artifact.get("cpu_time_s", 0.0)) if artifact else 0.0
        max_mem = float(artifact.get("max_rss_mb", 0.0)) if artifact else 0.0
        violation = None
        if timed_out:
            violation = "timeout"
        elif max_mem > mem_limit:
            violation = f"memory_limit_exceeded:{max_mem:.0f}>{mem_limit:.0f}"
        return SandboxResult(stdout=stdout[-4000:], stderr=stderr[-4000:], exit_code=code, runtime_s=runtime,
                             cpu_time_s=cpu_time, max_memory_mb=max_mem, timed_out=timed_out,
                             resource_violation=violation, artifact=artifact, executor=self.name)


class DockerExecutor:
    name = "docker"

    def __init__(self, image: Optional[str] = None):
        self.image = image or self.default_image()
        self.image_id: Optional[str] = None

    @staticmethod
    def content_hash() -> str:
        h = hashlib.sha256()
        for f in ("Dockerfile", "runner.py"):
            h.update((SANDBOX_DIR / f).read_bytes())
        return h.hexdigest()[:8]

    @classmethod
    def default_image(cls) -> str:
        base = os.environ.get("AGM_SANDBOX_IMAGE", "agm-lab-sandbox:0.1")
        return f"{base.split(':')[0]}:{cls.content_hash()}"

    @staticmethod
    def available() -> bool:
        if not shutil.which("docker"):
            return False
        try:
            return subprocess.run(["docker", "info"], capture_output=True, timeout=20).returncode == 0
        except Exception:
            return False

    def ensure_image(self) -> str:
        r = subprocess.run(["docker", "image", "inspect", self.image, "--format", "{{.Id}}"], capture_output=True, text=True)
        if r.returncode != 0:
            b = subprocess.run(["docker", "build", "-q", "-t", self.image, str(SANDBOX_DIR)], capture_output=True, text=True, timeout=600)
            if b.returncode != 0:
                raise RuntimeError(f"sandbox image build failed: {b.stderr[-2000:]}")
            r = subprocess.run(["docker", "image", "inspect", self.image, "--format", "{{.Id}}"], capture_output=True, text=True)
        self.image_id = r.stdout.strip()
        return self.image_id

    def run(self, payload: Dict[str, Any], limits: Dict[str, Any]) -> SandboxResult:
        if self.image_id is None:
            self.ensure_image()
        timeout = float(limits.get("timeout_s", 30))
        mem_mb = max(16, int(limits.get("memory_mb", 512)))
        cpus = max(0.1, float(limits.get("cpu", 1.0)))
        name = f"agm-{uuid.uuid4().hex[:12]}"
        cmd = ["docker", "run", "-i", "--name", name,
               "--network", "none",
               "--cpus", f"{cpus:.2f}",
               "--memory", f"{mem_mb}m", "--memory-swap", f"{mem_mb}m",
               "--pids-limit", "64",
               "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges",
               "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
               "--user", "65534:65534",
               self.image]
        t0 = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(cmd, input=json.dumps(payload), capture_output=True, text=True, timeout=timeout + 2.0)  # 2s grace for container start-up
            stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as e:
            subprocess.run(["docker", "kill", name], capture_output=True)
            stdout = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            code, timed_out = -9, True
        runtime = time.monotonic() - t0
        insp = subprocess.run(["docker", "inspect", name, "--format", "{{.State.OOMKilled}} {{.State.ExitCode}}"],
                              capture_output=True, text=True)
        oom = insp.stdout.strip().startswith("true")
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        artifact = _parse_output(stdout)
        cpu_time = float(artifact.get("cpu_time_s", 0.0)) if artifact else 0.0
        max_mem = float(artifact.get("max_rss_mb", 0.0)) if artifact else 0.0
        # The runner measures its own wall time; the difference is container overhead. Report both.
        violation = None
        if timed_out:
            violation = "timeout"
        elif oom or code == 137:
            violation = f"memory_limit_exceeded:{mem_mb}mb"
        return SandboxResult(stdout=stdout[-4000:], stderr=stderr[-4000:], exit_code=code, runtime_s=runtime,
                             cpu_time_s=cpu_time, max_memory_mb=max_mem, timed_out=timed_out,
                             resource_violation=violation, artifact=artifact, executor=self.name)


def get_executor(name: Optional[str] = None):
    name = (name or os.environ.get("AGM_EXECUTOR", "docker")).lower()
    if name == "docker":
        if not DockerExecutor.available():
            raise RuntimeError("Docker is not available; set AGM_EXECUTOR=process for an unisolated run")
        return DockerExecutor()
    if name == "process":
        return ProcessExecutor()
    raise ValueError(f"unknown executor {name}")
