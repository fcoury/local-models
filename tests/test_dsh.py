#!/usr/bin/env python3
"""Offline check: two model routes, idempotent preparation, invalid metadata."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
dsh = Path(os.environ.get('MODELCTL_DSH_ROOT', str(Path.home() / 'code/deepseek-harness')))
spec = importlib.util.spec_from_file_location('dsh_config', root / 'bin/modelctl-dsh.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    env = dict(os.environ, LOCAL_MODEL_STATE_HOME=tmp)
    for model in ['deepseek-v4.1-flash-q2-32k', 'deepseek-v4-flash', 'qwen3.8-27b']:
        metadata = json.loads(subprocess.check_output([root / 'bin/modelctl', 'endpoint', model, '--json'], env=env))
        target = home / model
        for profile in ['web', 'headless']:
            module.prepare(dsh, target, profile, metadata)
            patch = {row['id']: row for row in json.loads((target / f'modelctl-{profile}.patch.yml').read_text()) if 'id' in row}
            if model.startswith('deepseek'):
                config = patch['llm-deepseek']['config']
                assert config['thinking'] == 'disabled'
                assert config['models'][0]['contextWindow'] == metadata['context']
                assert config['maxTokens'] == metadata['output']
            else:
                config = patch['llm-pi-ai']['config']['providers']['modelctl-local']
                assert config['models'][0]['contextWindow'] == 131072
                assert config['reasoning'] == 'off'
                assert config['compat']['chatTemplateKwargs']['enable_thinking'] == {'$var': 'thinking.enabled'}
            if profile == 'headless':
                assert patch['compaction-basic']['config']['retainTokens'] == 4096
                assert patch['compaction-basic']['config']['thresholdRatio'] == 0.6
                assert patch['compaction-basic']['config']['maxTokens'] == 8192
                assert patch['tool-subagent']['disabled'] and patch['tool-ralph']['disabled']
                assert patch['skill-filesystem']['disabled'] and patch['tool-skill']['disabled']
        preset = (target / '.agent-presets/modelctl-ptc/agent.cordis.yml').read_text()
        assert '- id: delegation\n  disabled: true' in preset
        assert '- id: skill-filesystem\n  disabled: true' in preset
        assert '- id: tool-skill\n  disabled: true' in preset
        assert 'mode: ptc' in preset and '"maxTokens": 8192' in preset
        assert '"thresholdRatio": 0.6' in preset
        settings = target / 'settings.yaml'
        settings.write_text('user preferences\n')
        module.prepare(dsh, target, 'web', metadata)
        assert settings.read_text() == 'user preferences\n'
        assert (target / '.agent-presets/modelctl-ptc/agent.cordis.yml').read_text() == preset
        try:
            module.prepare(dsh, home / 'invalid', 'web', dict(metadata, context=None))
        except ValueError:
            pass
        else:
            raise AssertionError('Incomplete model metadata accepted')
        assert not (home / 'invalid').exists()
    # Use DSH's own resolver too: a syntactically valid catalog can still be rejected.
    subprocess.run(['node', '--input-type=module', '-', str(dsh), str(home / 'qwen3.8-27b')],
        input="""import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const {Config,resolveProfiles}=await import(pathToFileURL(process.argv[2]+'/packages/llm/llm-pi-ai/lib/types/config.js'));
const rows=JSON.parse(fs.readFileSync(process.argv[3]+'/modelctl-web.patch.yml','utf8'));
const config=Config(rows.find(x=>x.id==='llm-pi-ai').config);
if (!resolveProfiles(config.providers).has('modelctl-local')) throw Error('Missing local route');
""", text=True, check=True)
    # Exercise the real Bash entry point, cwd and argument forwarding without inference.
    fakebin = home / 'bin'
    fakebin.mkdir()
    for name, script in {
        'curl': '#!/bin/sh\nexit 0\n',
        'node': '#!/usr/bin/env python3\nimport json, os, sys\nprint(json.dumps(dict(args=sys.argv[1:], cwd=os.getcwd(), home=os.environ["DSH_HOME"])))\n',
    }.items():
        path = fakebin / name
        path.write_text(script)
        path.chmod(0o755)
    env.update(PATH=str(fakebin) + os.pathsep + env['PATH'], MODELCTL_DSH_HOME=str(home / 'launch'))
    for profile in ['web', 'headless']:
        result = json.loads(subprocess.check_output(
            [root / 'bin/modelctl', 'dsh', 'deepseek-v4.1-flash-q2-32k', profile, 'a quoted task'],
            cwd=tmp, env=env))
        assert Path(result['cwd']).resolve() == home.resolve()
        assert result['args'][-1] == 'a quoted task'
        assert ('--host' in result['args']) == (profile == 'web')
print('DSH offline checks passed (DeepSeek and Qwen; no inference)')
