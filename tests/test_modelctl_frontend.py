#!/usr/bin/env python3
"""Offline checks for the modelctl front end. No model is loaded or service touched."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'qwen3.8-flash-next-ud-q4-k-xl'
INKLING = 'inkling-2-mini-mlx-8bit'
BONSAI = 'ternary-bonsai-2.5-27b-pq2-mtp'
FLASH = 'qwen3.8-flash-next-iq-mlx-4.7bpw'
sys.dont_write_bytecode = True

with tempfile.TemporaryDirectory() as temp:
    temp = Path(temp).resolve()
    store, state, project = temp / 'models', temp / 'state', temp / 'project'
    for folder in (store, state, project):
        folder.mkdir()
    env = dict(os.environ, LOCAL_MODEL_STATE_HOME=str(state), NO_COLOR='1')

    def run(*args, script='modelctl', cwd=project, **extra):
        return subprocess.run([ROOT / 'bin' / script, *args], cwd=cwd, env=dict(env, **extra),
                              capture_output=True, text=True, stdin=subprocess.DEVNULL)

    # Legacy profiles: identical output and exit codes through the front end.
    ids = [l.split('\t')[0] for l in run('__complete', 'all', script='modelctl-legacy').stdout.splitlines()]
    assert len(ids) == 29
    for model in ids:
        for args in (['path', model], ['endpoint', model], ['endpoint', model, '--json'],
                     ['endpoint', model, '--bogus']):
            old, new = run(*args, script='modelctl-legacy'), run(*args)
            assert (old.returncode, old.stdout, old.stderr) == (new.returncode, new.stdout, new.stderr), args
    for scope in ('all', 'models', 'runnable', 'services', 'omp'):
        old = run('__complete', scope, script='modelctl-legacy').stdout
        new = run('__complete', scope).stdout
        added = [l.split('\t')[0] for l in new[len(old):].splitlines()]
        assert new.startswith(old) and added == ([FLASH, 'deepseek-v4.1-flash-sushi-stq-175-v2'] if scope == 'omp' else []) + [MODEL, INKLING, BONSAI], scope
    assert run('__complete', 'bogus').returncode == 2
    assert [l.split('\t')[0] for l in run('__names', 'pi').stdout.splitlines()] == [FLASH, 'flash', 'deepseek-v4.1-flash-sushi-stq-175-v2', 'deepseek', MODEL, 'flash-ud', INKLING, 'inkling', BONSAI, 'bonsai']
    names = [l.split('\t')[0] for l in run('__names', 'services').stdout.splitlines()]
    assert {'flash', 'flash-ud', 'deepseek', MODEL} <= set(names)

    # Aliases resolve everywhere; mistakes get a suggestion and the old exit code.
    assert run('path', 'flash').stdout == run('path', 'qwen3.8-flash-next-iq-mlx-4.7bpw').stdout
    assert json.loads(run('endpoint', 'flash-ud', '--json').stdout) == dict(
        id=MODEL, base_url='http://127.0.0.1:8089/v1', api_model='qwen3.8-flash-next-ud',
        context=65536, output=16384)
    typo = run('start', 'flsh')
    assert typo.returncode == 2 and 'Unknown model: flsh. Did you mean flash' in typo.stderr
    for args in (['bogus'], ['start'], ['use'], ['use', 'vim', 'flash-ud'], ['list', 'extra'],
                 ['use', 'pi', 'hy4-flash-q4-k-m'], ['dsh', 'flash-ud'], ['stop', 'minimax-music3']):
        result = run(*args)
        assert result.returncode == 2 and 'Traceback' not in result.stderr, (args, result)

    # modelbench reads the first two columns of piped status.
    row = run('status', MODEL).stdout.split()
    assert row[0] == MODEL and row[1] in ('running', 'stopped', 'external', 'unverified'), row
    rows = json.loads(run('list', '--json').stdout)
    assert len(rows) == 32 and len({r['name'] for r in rows}) == 32

    # Load the module against a tiny fake store to test verification and generated config.
    files = []
    folder = store / 'gguf/m'
    folder.mkdir(parents=True)
    for name, body in (('a.gguf', b'weights'), ('mmproj.gguf', b'eyes')):
        (folder / name).write_bytes(body)
        import hashlib
        files.append(dict(path=name, size=len(body), sha256=hashlib.sha256(body).hexdigest()))
    binary = store / 'runtime/llama-server'
    binary.parent.mkdir()
    binary.write_bytes(b'runtime')
    binary.chmod(0o755)
    manifest = temp / 'manifest.json'
    manifest.write_text(json.dumps(dict(revision='r' * 40, files=files)))
    home = temp / 'home'
    (home / '.omp/agent/extensions').mkdir(parents=True)
    (home / '.pi/agent').mkdir(parents=True)
    (home / '.pi/agent/settings.json').write_text('{"theme": "dark", "defaultProvider": "strata"}')
    os.environ.update(MODEL_HOME=str(store), LOCAL_MODEL_STATE_HOME=str(state), HOME=str(home))
    loader = importlib.machinery.SourceFileLoader('modelctl', str(ROOT / 'bin/modelctl'))
    spec = importlib.util.spec_from_loader('modelctl', loader)
    ctl = importlib.util.module_from_spec(spec)
    loader.exec_module(ctl)
    ctl.Out.quiet = True
    entry = next(m for m in ctl.tomllib.loads((ROOT / 'models.toml').read_text())['models'] if m['id'] == MODEL)
    real = ctl.Model(entry)
    command = real.command()
    assert command[command.index('--ctx-size') + 1] == '131072'
    assert command[command.index('--parallel') + 1] == '2' and '--no-kv-unified' in command
    assert json.loads(command[-1]) == {'reasoning_effort': 'medium'}
    assert sum(f['size'] for f in real.manifest['files']) == entry['bytes']
    # mlx-serve profiles load a directory; their files are checked inside it.
    inkling = ctl.Model(next(m for m in ctl.tomllib.loads((ROOT / 'models.toml').read_text())['models']
                             if m['id'] == INKLING))
    command = inkling.command()
    assert command[:3] == [str(inkling.binary), '--model', str(inkling.path)] and inkling.folder == inkling.path
    assert command[command.index('--host') + 1] == '127.0.0.1'
    assert inkling.api == inkling.path.name and inkling.max_output <= inkling.entry['harness']['reserve_tokens']
    assert real.folder == real.path.parent
    assert sum(f['size'] for f in inkling.manifest['files']) == inkling.entry['bytes']
    model = ctl.Model(dict(entry, path='gguf/m/a.gguf', manifest=str(manifest),
                           runtime_path='runtime/llama-server',
                           runtime_sha256=hashlib.sha256(b'runtime').hexdigest()))

    def refused(message):
        try:
            ctl.verify(model)
        except ctl.Failure as error:
            assert message in str(error), error
        else:
            raise AssertionError('accepted: ' + message)

    refused('has not been verified')
    ctl.doctor(model)
    ctl.verify(model)
    (folder / 'a.gguf.aria2').touch()
    refused('incomplete transfer')
    (folder / 'a.gguf.aria2').unlink()
    (folder / 'a.gguf').write_bytes(b'wEights')       # same size, different content
    refused('has not been verified')
    try:
        ctl.doctor(model)
    except ctl.Failure as error:
        assert 'SHA-256 mismatch' in str(error)
    else:
        raise AssertionError('doctor accepted changed weights')
    assert not model.receipt.exists()
    (folder / 'a.gguf').write_bytes(b'weights')
    ctl.doctor(model)
    binary.write_bytes(b'rebuilt')
    refused('runtime does not match')

    # Harness configs: isolated, per model, and never written to the user's own directories.
    omp_home, omp, level = ctl.prepare_omp(model)
    config = json.loads((omp_home / 'models.yml').read_text())['providers']['modelctl-flash-ud']
    assert config['models'][0]['compat']['reasoningDisableMode'] == 'none-effort'
    assert config['models'][0]['compat']['thinkingFormat'] == 'openai' and level == 'medium'
    assert (omp_home / 'extensions').is_symlink()
    pi_home, pi, _ = ctl.prepare_pi(model)
    levels = json.loads((pi_home / 'models.json').read_text())['providers']['modelctl']['models'][0]['thinkingLevelMap']
    assert levels == dict(off='none', minimal=None, low='low', medium='medium', high=None, xhigh='xhigh', max=None)
    settings = json.loads((pi_home / 'settings.json').read_text())
    assert settings['theme'] == 'dark' and settings['defaultProvider'] == 'modelctl'
    (pi_home / 'settings.json').write_text(json.dumps(dict(settings, theme='mine', defaultThinkingLevel='low')))
    ctl.prepare_pi(model)
    settings = json.loads((pi_home / 'settings.json').read_text())
    assert settings['theme'] == 'mine' and settings['defaultThinkingLevel'] == 'low'
    assert json.loads((home / '.pi/agent/settings.json').read_text())['defaultProvider'] == 'strata'
    assert omp_home != pi_home and str(omp_home).startswith(str(state))

    # A legacy-launched profile opts in with a harness table and caps output below its server limit.
    row = [FLASH, 'Flash', 'service', '18434', 'flash-api', '65536', '32768', '/x']
    entry = next(m for m in ctl.tomllib.loads((ROOT / 'models.toml').read_text())['models'] if m['id'] == FLASH)
    flash = ctl.Model(entry, row)
    assert not flash.data and flash.supports('pi') and flash.supports('omp')
    flash_home, _, _ = ctl.prepare_pi(flash)
    config = json.loads((flash_home / 'models.json').read_text())['providers']['modelctl']
    assert config['baseUrl'].endswith(':18434/v1') and flash_home != pi_home
    limits = entry['harness']
    assert config['models'][0]['maxTokens'] == limits['max_output'] <= limits['reserve_tokens']
    assert 'image' in config['models'][0]['input']

    # Existing configs get a larger reserve with the cap, keep a still larger one, and keep other edits.
    settings = json.loads((flash_home / 'settings.json').read_text())
    flash_omp, _, _ = ctl.prepare_omp(flash)
    for before, after in ((16384, limits['reserve_tokens']), (30000, 30000)):
        settings['compaction'] = dict(enabled=False, reserveTokens=before, keepRecentTokens=5)
        (flash_home / 'settings.json').write_text(json.dumps(settings))
        (flash_omp / 'config.yml').write_text(
            f'theme: mine\ncompaction:\n  keepRecentTokens: 5\n  reserveTokens: {before}\n')
        ctl.prepare_pi(flash)
        ctl.prepare_omp(flash)
        assert json.loads((flash_home / 'settings.json').read_text())['compaction'] == dict(
            enabled=False, reserveTokens=after, keepRecentTokens=5)
        assert (flash_omp / 'config.yml').read_text() == (
            f'theme: mine\ncompaction:\n  keepRecentTokens: 5\n  reserveTokens: {after}\n')

    # DeepSeek offers max above xhigh.
    row = ['deepseek-v4.1-flash-sushi-stq-175-v2', 'DeepSeek', 'service', '18352', 'ds-api', '65536', '32768', '/x']
    entry = next(m for m in ctl.tomllib.loads((ROOT / 'models.toml').read_text())['models'] if m['id'] == row[0])
    deep = ctl.Model(entry, row)
    home, _, level = ctl.prepare_pi(deep)
    levels = json.loads((home / 'models.json').read_text())['providers']['modelctl']['models'][0]['thinkingLevelMap']
    assert levels['max'] == 'max' and levels['medium'] == 'medium' and levels['minimal'] is None and level == 'off'
    home, _, _ = ctl.prepare_omp(deep)
    config = json.loads((home / 'models.yml').read_text())['providers']['modelctl-deepseek']['models'][0]
    assert config['thinking']['effortMap'] == {} and config['input'] == ['text', 'image']
    assert config['thinking']['defaultLevel'] == 'low'

    # Harnesses are refused inside the model store, including through a symlink.
    link = temp / 'link'
    link.symlink_to(store)
    for place in (store, folder, link / 'gguf'):
        os.chdir(place)
        try:
            ctl.check_directory()
        except ctl.Failure:
            pass
        else:
            raise AssertionError(f'harness allowed in {place}')
    os.chdir(project)
    ctl.check_directory()

    # Guardrails, with process state supplied instead of read from the machine.
    class Fake:
        services, ports, servers = {}, {}, []

        def unmanaged(self):
            return self.servers

    class Shelf:
        models = [model]
    fake = Fake()
    ctl.check_exclusive(model, Shelf, fake)
    big = dict(pid=1, port=9931, rss=40 * ctl.GIB, command='llama-server')
    fake.servers = [big]
    for force, blocked in ((False, True), (True, False)):
        try:
            ctl.check_exclusive(model, Shelf, fake, force)
        except ctl.Failure:
            assert blocked
        else:
            assert not blocked
    fake.servers = [dict(big, rss=ctl.GIB)]
    ctl.check_exclusive(model, Shelf, fake)
    legacy = ctl.Model({'id': 'other', 'alias': 'other'}, ['other', 'Other', 'service', '1', 'o', '', '', '/x'])
    Shelf.models, fake.servers, fake.ports = [model, legacy], [], {model.port: 5}
    try:
        ctl.check_exclusive(legacy, Shelf, fake)
    except ctl.Failure as error:
        assert 'flash-ud' in str(error)
    else:
        raise AssertionError('second large model allowed')

    for args, expected in (('/opt/homebrew/bin/llama-server -m x', True), ('llama-server -hf a/b', True),
                           ('/a/venv/bin/python /a/venv/bin/omlx serve', True),
                           ('/a/Python.app/Contents/MacOS/Python /a/venv/bin/omlx serve', True),
                           ('/x/sushi-macos-arm64/sushi serve --model y', True),
                           ('vim notes/sushi', False), ('node server.js', False),
                           ('rg llama-server', False), ('python3 -m http.server 8000', False)):
        assert bool(ctl.is_model_server(args)) == expected, args
    for text, expected in (('01:02', 62), ('02:00:00', 7200), ('1-00:00:01', 86401)):
        assert ctl.seconds(text) == expected

print('modelctl front end checks passed (no inference)')
