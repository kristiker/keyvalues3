"""
Test parser against Dota 2 Particles.

Run with:
    python -m pytest tests/stresstest.py -s
"""

from pathlib import Path

# dota 2 path
dota2_path =  Path(r'D:\Games\steamapps\common\dota 2 beta')
CAP = 100

import keyvalues3
import time

start = time.time()
count = 0
def finish(count: int):
    print(f"Ran through {count} files in", time.time() - start, "seconds")

for vpcf in (dota2_path / "content").glob("**/*.vpcf"):
    if count > CAP:
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
