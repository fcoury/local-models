#!/usr/bin/env python3
"""Generate owned DSH overlays from modelctl endpoint JSON; no model requests."""
import json
from pathlib import Path
import re
import sys


def prepare(root, home, profile, model):
    if profile not in ('web', 'headless'):
        raise ValueError('DSH profile must be web or headless')
    if (not isinstance(model.get('api_model'), str) or not model['api_model']
            or any(type(model.get(k)) is not int or model[k] < 1024 for k in ('context', 'output'))
            or model['output'] >= model['context']):
        raise ValueError('Model needs an API model name and valid context/output metadata in modelctl')
    from urllib.parse import urlparse
    url = urlparse(model['base_url'])
    if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.username or url.password:
        raise ValueError('modelctl DSH requires a local HTTP endpoint')
    context, output = model['context'], model['output']
    # Reserve room for DSH's 8192-token checkpoint; truncated summaries are discarded.
    compaction = dict(thresholdRatio=0.6, retainTokens=min(4096, context // 8),
                      maxTokens=min(8192, output, context // 4))
    catalog = dict(id=model['api_model'], name=model['id'], contextWindow=context, maxTokens=output)
    deepseek = model['api_model'].startswith('deepseek-')
    provider = 'deepseek-official' if deepseek else 'modelctl-local'
    patch = [dict(id='agent-default-model', config=dict(provider=provider, model=model['api_model'])),
             dict(id='session-title-llm', disabled=True)]
    if deepseek:
        patch += [dict(id='llm-pi-ai', disabled=True), dict(id='llm-deepseek', config=dict(
            apiKeyEnv='MODELCTL_DSH_API_KEY', baseURL=model['base_url'], thinking='disabled',
            reasoningEffort='off', maxTokens=output, defaultContextWindow=context,
            models=[dict(catalog, inputModalities=['text'])]))]
    else:
        qwen = model['id'].startswith('qwen')
        compat = dict(supportsStore=False, supportsDeveloperRole=False, maxTokensField='max_tokens',
                      supportsReasoningEffort=True, thinkingFormat='qwen-chat-template' if qwen else 'openai')
        if qwen:
            compat['chatTemplateKwargs'] = dict(enable_thinking={'$var': 'thinking.enabled'})
        route = dict(apiKeyEnv='MODELCTL_DSH_API_KEY', api='openai-completions',
                     baseURL=model['base_url'], reasoning='off', compat=compat,
                     models=[dict(catalog, input=['text'], reasoningEfforts={'off': None if qwen else 'none', 'high': 'high'})])
        patch += [dict(id='llm-deepseek', disabled=True),
                  dict(id='llm-pi-ai', config=dict(providers={provider: route}))]
    # Reuse upstream PTC, including its sandbox/approval policies. Fail on layout drift.
    source = root / 'packages/preset/agent-presets/presets/ptc'
    preset = (source / 'agent.cordis.yml').read_text()
    for row in ('delegation', 'tool-web', 'skill-filesystem', 'tool-skill'):
        preset, count = re.subn(rf'^(- id: {row}\n)', r'\1  disabled: true\n', preset, flags=re.M)
        if count != 1:
            raise ValueError(f'Upstream PTC changed: expected one {row} row')
    preset, count = re.subn(
        r'^(    - id: compaction-basic\n      name: [^\n]+\n)',
        lambda m: m[0] + '      config: ' + json.dumps(compaction) + '\n', preset, flags=re.M)
    if count != 1:
        raise ValueError('Upstream PTC changed: expected one compaction-basic row')
    if profile == 'web':
        patch += [dict(id='agent-presets', config=dict(default='modelctl-ptc', includeUserRoot=True)),
                  dict(id='directory-picker', disabled=True),
                  dict(insert=[dict(id='modelctl-directory-picker', name='@deepseek-ai/dsh-host-directory-picker-browse'),
                               dict(id='modelctl-directory-picker-ui',
                                    name='@deepseek-ai/dsh-client-ui-directory-picker-browse')])]
    else:
        patch += [dict(id='tools', config=dict(mode='ptc')), dict(id='compaction-basic', config=compaction)]
        patch += [dict(id=row, disabled=True) for row in (
            'tool-subagent-control', 'tool-subagent-list-agents', 'tool-subagent', 'tool-subagent-fork',
            'tool-workflow', 'tool-ralph', 'tool-web', 'skill-filesystem', 'tool-skill')]
    target = home / '.agent-presets/modelctl-ptc'
    target.mkdir(parents=True, exist_ok=True)
    # These files are generated; user settings, sessions and copied presets are untouched.
    for path, contents in (
        (target / 'preset.yml', 'name: Local PTC\ndescription: PTC coding tools, thinking off, no delegation, web search or skills\norder: 0\n'),
        (target / 'agent.cordis.yml', preset),
        (home / f'modelctl-{profile}.patch.yml', json.dumps(patch, indent=2) + '\n'),
    ):
        temp = path.with_suffix(path.suffix + '.tmp')
        temp.write_text(contents)
        temp.replace(path)


if __name__ == '__main__':
    try:
        prepare(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], json.load(sys.stdin))
    except (ValueError, KeyError, OSError) as error:
        sys.exit(f'modelctl dsh: {error}')
