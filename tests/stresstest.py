"""
Test parser against Dota 2 Particles.

On hot runs:
    Ran through 100 files in 2.6 seconds
    Ran through 1000 files in 27 seconds

Run with:
    python -m pytest tests/stresstest.py -s
"""

from pathlib import Path

# dota 2 path
dota2_path = Path(r"D:\Games\steamapps\common\dota 2 beta")
MAX_FILES = 100

import keyvalues3
import time

start = time.time()
count = 0


def finish(count: int):
    print(f"Ran through {count} files in", time.time() - start, "seconds")


for vpcf in (dota2_path / "content").glob("**/*.vpcf"):
    if count >= MAX_FILES:
        break
    try:
        kv = keyvalues3.read(vpcf)
    except (keyvalues3.KV3DecodeError, KeyboardInterrupt):
        print(vpcf)
        finish(count)
        raise

    print(kv)
    count += 1

finish(count)
