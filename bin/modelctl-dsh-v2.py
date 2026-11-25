#!/usr/bin/env python3
"""Prepare DSH 0.2 profiles without touching user settings or earlier sessions."""
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse


def prepare(root, home, profile, model):
    if profile not in ('web', 'headless'):
        raise ValueError('DSH profile must be web or headless')
    context, output = model.get('context'), model.get('output')
    if (not isinstance(model.get('api_model'), str) or not model['api_model']
            or any(type(n) is not int or n < 1024 for n in (context, output))
            or output >= context):
        raise ValueError('Model needs an API model name and valid context/output metadata')
    url = urlparse(model['base_url'])
    if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.username or url.password:
        raise ValueError('modelctl DSH requires a local HTTP endpoint')
    # Bound interactive responses and leave explicit space for the v2 summarizer.
    output = min(output, 8192, context // 4)
    compaction = dict(auto=True, headroomTokens=min(8192, context // 8),
                      thresholdRatio=0.6, retainTokens=min(4096, context // 8),
                      maxTokens=min(8192, output, context // 4))
    catalog = dict(id=model['api_model'], name=model['id'], contextWindow=context, maxTokens=output)
    deepseek = model['api_model'].startswith('deepseek-')
    qwen = model['id'].startswith('qwen')
    sushi = model['id'] in ('deepseek-v4.1-flash-sushi-stq-175', 'deepseek-v4.1-flash-sushi-stq-175-v2')
    mtp_qwen = model['id'] == 'qwen3.8-27b-abliterated-oq8e-mtp'
    provider = 'deepseek-official' if deepseek else 'modelctl-local'
    patch = [dict(id='agent-default-model', config=dict(provider=provider, model=model['api_model'])),
             dict(id='session-title-llm', disabled=True)]
    if deepseek:
        patch.extend([dict(id='llm-pi-ai', disabled=True), dict(id='llm-deepseek', config=dict(
            apiKeyEnv='MODELCTL_DSH_API_KEY', baseURL=model['base_url'],
            thinking='enabled' if sushi else 'disabled', reasoningEffort='off',
            maxTokens=output, defaultContextWindow=context,
            # Revision 2 runs with its 0.77 GiB vision encoder loaded.
            models=[dict(catalog, inputModalities=['text', 'image']
                         if model['id'] == 'deepseek-v4.1-flash-sushi-stq-175-v2' else ['text'])]))])
    else:
        compat = dict(supportsStore=False, supportsDeveloperRole=False, maxTokensField='max_tokens',
                      supportsReasoningEffort=True, thinkingFormat='qwen-chat-template' if qwen else 'openai')
        if qwen:
            compat['chatTemplateKwargs'] = dict(enable_thinking={'$var': 'thinking.enabled'})
        route = dict(apiKeyEnv='MODELCTL_DSH_API_KEY', api='openai-completions',
                     baseURL=model['base_url'], reasoning='high' if mtp_qwen else 'off', compat=compat,
                     models=[dict(catalog, input=['text'], reasoningEfforts={
                         'off': None if qwen else 'none', 'high': 'medium' if mtp_qwen else 'high'})])
        patch.extend([dict(id='llm-deepseek', disabled=True), dict(id='llm-deepseek-account', disabled=True),
                      dict(id='llm-pi-ai', config=dict(providers={provider: route}))])
    source = ''
    if profile == 'web':
        patch.extend([dict(id='agent-preset-registry', config={'default': 'modelctl-ptc'}),
                      dict(id='directory-picker', disabled=True),
                      dict(insert=[dict(id='modelctl-directory-picker', name='@deepseek-ai/dsh-host-directory-picker-browse'),
                                   dict(id='modelctl-directory-picker-ui', name='@deepseek-ai/dsh-client-ui-directory-picker-browse')])])
        source = (root / 'packages/bundle/web-app/presets/ptc.patch.yml').read_text()
        source = source[source.index('- insert:'):]
        source = source.replace('id: preset-ptc', 'id: preset-modelctl-ptc', 1)
        source = source.replace('id: ptc\n', 'id: modelctl-ptc\n', 1)
        for row in ('delegation', 'tool-web', 'skill-filesystem', 'tool-skill'):
            source, count = re.subn(rf'^(          - id: {row}\n)', r'\1            disabled: true\n', source, flags=re.M)
            if count != 1:
                raise ValueError(f'Upstream PTC changed: expected one {row} row')
        source, count = re.subn(r'^(              - id: compaction-basic\n                name: [^\n]+\n)',
                                lambda m: m[0] + '                config: ' + json.dumps(compaction) + '\n',
                                source, flags=re.M)
        if count != 1:
            raise ValueError('Upstream PTC changed: expected one compaction-basic row')
    else:
        patch.extend([dict(id='tools', config=dict(mode='ptc')), dict(id='compaction-basic', config=compaction)])
        patch.extend(dict(id=row, disabled=True) for row in (
            'tool-subagent-control', 'tool-subagent-list-agents', 'tool-subagent', 'tool-subagent-fork',
            'tool-workflow', 'tool-web', 'skill-filesystem', 'tool-skill'))
    home.mkdir(parents=True, exist_ok=True)
    destination = home / f'modelctl-{profile}.patch.yml'
    temporary = destination.with_suffix('.tmp')
    temporary.write_text(''.join('- ' + json.dumps(row) + '\n' for row in patch) + source)
    temporary.replace(destination)


if __name__ == '__main__':
    try:
        prepare(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], json.load(sys.stdin))
    except (ValueError, KeyError, OSError, IndexError) as error:
        sys.exit(f'modelctl dsh: {error}')
