#!/usr/bin/env python3
"""Phase 1 host validation: prints what the laboratory needs and whether it is present."""
import platform
import shutil
import subprocess
import sys

import psutil

REQUIRED_MODULES = ["fastapi", "pydantic", "sqlalchemy", "yaml", "psutil", "pytest", "uvicorn"]


def main() -> int:
    ok = True
    print(f"python      : {sys.version.split()[0]}  ({'ok' if sys.version_info >= (3, 10) else 'need >= 3.10'})")
    ok &= sys.version_info >= (3, 10)
    print(f"platform    : {platform.system()} {platform.release()}")
    print(f"cpu         : {psutil.cpu_count(logical=False)} cores / {psutil.cpu_count()} threads")
    mem = psutil.virtual_memory().total / 2**30
    print(f"memory      : {mem:.1f} GB total, {psutil.virtual_memory().available / 2**30:.1f} GB available  ({'ok' if mem >= 6 else 'low'})")
    disk = shutil.disk_usage(".").free / 2**30
    print(f"disk free   : {disk:.1f} GB  ({'ok' if disk >= 5 else 'low'})")
    for m in REQUIRED_MODULES:
        try:
            __import__(m)
            print(f"module      : {m:12s} ok")
        except ImportError:
            print(f"module      : {m:12s} MISSING (pip install -r requirements.txt)")
            ok = False
    if shutil.which("docker"):
        r = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"], capture_output=True, text=True)
        if r.returncode == 0:
            print(f"docker      : server {r.stdout.strip()} ok (sandbox executor available)")
        else:
            print("docker      : installed but not usable by this user (sandbox executor unavailable; AGM_EXECUTOR=process only)")
    else:
        print("docker      : not installed (sandbox executor unavailable; AGM_EXECUTOR=process only)")
    print(f"git         : {'ok' if shutil.which('git') else 'MISSING'}")
    print("result      :", "host ready" if ok else "host NOT ready")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
