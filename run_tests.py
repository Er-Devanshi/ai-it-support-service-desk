#!/usr/bin/env python
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
    cwd="c:\\Users\\srish\\Documents\\ai-it-support-service-desk"
)
sys.exit(result.returncode)
