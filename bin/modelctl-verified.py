#!/usr/bin/env python3
"""Check retained verification receipts and current file sizes without rehashing weights."""
import hashlib
import json
from pathlib import Path
import sys

PINS = {
    'flash-next-iq': ('3514842eca3b8d518fd388709a591cfda0e0caa76a70668815bc790c729eb969', 113),
    'deepseek': ('21bb4747920dcf451e96aa76945c239a82971a664d384aa098a74fde3edfa746', 96),
    'deepseek-v2': ('54cfef0c49233821d4a40bab8b120dc7055ca40de306cdaaef8dab4f48207208', 101),
    'qwen': ('a77f3c572de6d6a9a4a92595fce892fdc9ca555ac59753c18e83fea97cdd0cae', 20),
}

def check(kind, root, receipt):
    digest, count = PINS[kind]
    raw = receipt.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        return False
    data = json.loads(raw)
    files = data['files']
    if len(files) != count or any(root.rglob('*.aria2')):
        return False
    if kind == 'deepseek' and (data.get('verified') is not True or data.get('revision') != '07fec972538639726b868f81e89d9d4f5005fe10'):
        return False
    if kind == 'deepseek-v2' and (data.get('verified') is not True or data.get('revision') != '89630812557263bb7a7582fb1f30455573511155'):
        return False
    if kind == 'flash-next-iq' and (data.get('verified') is not True or data.get('revision') != 'a0e89db090a3e4b2e8ea2118fe9d0324d3854aca'):
        return False
    for row in files:
        name = Path(row['file'])
        if name.is_absolute() or '..' in name.parts:
            return False
        target = root / name
        if not target.is_file() or target.stat().st_size != row['bytes']:
            return False
        if kind in ('deepseek', 'deepseek-v2', 'flash-next-iq') and (row.get('verified') is not True or row.get('actual') != row.get('expected')):
            return False
        if kind == 'qwen' and name.suffix == '.safetensors' and not row.get('lfs_hash_checked'):
            return False
    return True

if __name__ == '__main__':
    try:
        if not check(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])):
            sys.exit(1)
    except (OSError, ValueError, KeyError, IndexError):
        sys.exit(1)
