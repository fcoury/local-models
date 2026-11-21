#!/usr/bin/env python3
"""Check the pinned Hy4 download receipt without rehashing either shard."""
import hashlib
import json
from pathlib import Path
import sys

RECEIPT_SHA256 = '1ca69a873f752fb0c56ac120ab61cdef471749ca2398a325a0befdf30da62a80'
REVISION = 'bcbc7db5dcf4162cc1e1b8ed6c65567e843ebe46'


def check(root, receipt):
    raw = receipt.read_bytes()
    if hashlib.sha256(raw).hexdigest() != RECEIPT_SHA256:
        return False
    data = json.loads(raw)
    files = data['shards']
    if (data.get('verified') is not True or data.get('revision') != REVISION
            or len(files) != 2 or any(root.glob('*.aria2'))):
        return False
    verified_at = receipt.stat().st_mtime_ns
    for row in files:
        target = root / Path(row['file']).name
        stamp = target.stat()
        if (not target.is_file() or stamp.st_size != row['bytes']
                or max(stamp.st_mtime_ns, stamp.st_ctime_ns) > verified_at
                or row.get('verified') is not True or row['actual'] != row['expected']):
            return False
    return True


if __name__ == '__main__':
    try:
        if not check(Path(sys.argv[1]), Path(sys.argv[2])):
            sys.exit(1)
    except (OSError, ValueError, KeyError, IndexError):
        sys.exit(1)
