#!/usr/bin/env python3
"""Check v2 overlays for all chat profiles without loading model weights."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
dsh = Path(os.environ.get('MODELCTL_DSH_ROOT', str(Path.home() / 'code/deepseek-harness.codex-modelctl-dsh-rc3')))
spec = importlib.util.spec_from_file_location('dsh_v2', root / 'bin/modelctl-dsh-v2.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    env = dict(os.environ, LOCAL_MODEL_STATE_HOME=tmp)
    rows = subprocess.check_output([root / 'bin/modelctl', '__complete', 'services'], env=env, text=True).splitlines()
    checked = []
    budgets = []
    for row in rows:
        model = row.split('\t')[0]
        meta = json.loads(subprocess.check_output([root / 'bin/modelctl', 'endpoint', model, '--json'], env=env))
        if not meta.get('api_model') or not meta.get('output'):
            continue
        checked.append(model)
        for profile in ('web', 'headless'):
            target = home / model
            module.prepare(dsh, target, profile, meta)
            content = (target / f'modelctl-{profile}.patch.yml').read_text()
            rows = [json.loads(line[2:]) for line in content.splitlines() if line.startswith('- {')]
            patch = {row['id']: row for row in rows if 'id' in row}
            assert patch['agent-default-model']['config']['model'] == meta['api_model']
            if model.startswith('deepseek'):
                config = patch['llm-deepseek']['config']
                assert config['baseURL'] == meta['base_url']
                assert config['models'][0]['contextWindow'] == meta['context']
                if model in ('deepseek-v4.1-flash-sushi-stq-175', 'deepseek-v4.1-flash-sushi-stq-175-v2'):
                    assert config['thinking'] == 'enabled'
                    assert config['reasoningEffort'] == 'off'
            else:
                route = patch['llm-pi-ai']['config']['providers']['modelctl-local']
                assert route['baseURL'] == meta['base_url']
                assert route['models'][0]['contextWindow'] == meta['context']
            if profile == 'web':
                assert patch['agent-preset-registry']['config']['default'] == 'modelctl-ptc'
                assert 'id: preset-modelctl-ptc' in content
                for entry in ('delegation', 'tool-web', 'skill-filesystem', 'tool-skill'):
                    assert f'- id: {entry}\n            disabled: true' in content
                assert '"thresholdRatio": 0.6' in content
                import re
                budget = json.loads(re.search(r'                config: (\{.*\})', content)[1])
                budgets.append(dict(policy=budget, context=meta['context'], output=min(meta['output'], 8192, meta['context'] // 4)))
            else:
                assert patch['tools']['config']['mode'] == 'ptc'
                assert patch['compaction-basic']['config']['thresholdRatio'] == 0.6
        try:
            module.prepare(dsh, home / 'invalid', 'web', dict(meta, output=None))
        except ValueError:
            pass
        else:
            raise AssertionError('Accepted invalid endpoint metadata')
    assert 'deepseek-v4.1-flash-sushi-stq-175' in checked
    assert 'deepseek-v4.1-flash-sushi-stq-175-v2' in checked
    assert 'qwen3.8-27b-abliterated-oq8e-mtp' in checked
    subprocess.run(['node', '--input-type=module', '-', str(dsh)], input="""
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const {resolveConfig,resolveTargetPolicy,resolveCompactSpec}=await import(pathToFileURL(process.argv[2]+'/packages/compaction/compaction-basic/lib/types/config.js'));
const target={provider:'local',model:'test'};
const rows=JSON.parse(process.env.DSH_TEST_BUDGETS);
for (const row of rows) {
 const policy=resolveTargetPolicy(resolveConfig(row.policy),target);
 const spec=resolveCompactSpec(policy,row.context,row.output);
 if (!(spec.thresholdTokens>0 && spec.thresholdTokens+row.output+row.policy.headroomTokens<=row.context)) throw Error('Invalid compaction budget');
}
let failed=false;
try { resolveCompactSpec(resolveTargetPolicy(resolveConfig({thresholdRatio:.6,retainTokens:4096,maxTokens:8192}),target),65536,32768); }
catch(e) { failed=String(e).includes('headroom'); }
if (!failed) throw Error('Original headroom failure did not reproduce');
""", text=True, env=dict(os.environ,DSH_TEST_BUDGETS=json.dumps(budgets)), check=True)
    print(f'DSH v2 overlay checks passed for {len(checked)} chat profiles')
