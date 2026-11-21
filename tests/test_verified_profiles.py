#!/usr/bin/env python3
"""Receipt identity, files, and interrupted-transfer guards for modelctl profiles."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verified', root / 'bin/modelctl-verified.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as tmp:
    model = Path(tmp) / 'model'
    model.mkdir()
    (model / 'weights.safetensors').write_bytes(b'weights')
    receipt = Path(tmp) / 'receipt.json'
    data = {'files': [{'file': 'weights.safetensors', 'bytes': 7, 'lfs_hash_checked': True}]}
    receipt.write_text(json.dumps(data))
    module.PINS['qwen'] = (hashlib.sha256(receipt.read_bytes()).hexdigest(), 1)
    assert module.check('qwen', model, receipt)
    (model / 'weights.safetensors.aria2').touch()
    assert not module.check('qwen', model, receipt)
    (model / 'weights.safetensors.aria2').unlink()
    (model / 'weights.safetensors').write_bytes(b'changed size')
    assert not module.check('qwen', model, receipt)
    receipt.write_text('{}')
    assert not module.check('qwen', model, receipt)

    (model / 'weights.safetensors').write_bytes(b'weights')
    digest = hashlib.sha256(b'weights').hexdigest()
    data = {'revision': '89630812557263bb7a7582fb1f30455573511155', 'verified': True,
            'files': [{'file': 'weights.safetensors', 'bytes': 7, 'expected': digest,
                       'actual': digest, 'verified': True}]}

    def pin_v2():
        receipt.write_text(json.dumps(data))
        module.PINS['deepseek-v2'] = (hashlib.sha256(receipt.read_bytes()).hexdigest(), 1)

    pin_v2()
    assert module.check('deepseek-v2', model, receipt)
    data['revision'] = '07fec972538639726b868f81e89d9d4f5005fe10'
    pin_v2()
    assert not module.check('deepseek-v2', model, receipt)
    data['revision'] = '89630812557263bb7a7582fb1f30455573511155'
    data['files'][0]['actual'] = '0' * 64
    pin_v2()
    assert not module.check('deepseek-v2', model, receipt)
print('Verification receipt checks passed')
