#!/usr/bin/env python3
"""Small coding eval: standard-library runner, fixed tools, independent graders."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from grading import grade

ROOT = Path(__file__).resolve().parent
DEFAULT_RUNS = Path.home()/'Library/Application Support/local-models/benchmarks/small-coding'
SYSTEM = ('Complete the supplied small coding task using the available tools. '
          'Read the relevant files, make the requested changes, and run the public checks. '
          'Only the explicitly allowed files may be written. Do not seek outside solutions. '
          'Your final response should briefly state what changed and which checks ran. '
          'Independent grading happens after your turn; you cannot access those checks.')
TOOLS = [
    {'type':'function','function':{'name':'read_file','description':'Read a UTF-8 file relative to the task workspace.','parameters':{'type':'object','properties':{'path':{'type':'string'}},'required':['path'],'additionalProperties':False}}},
    {'type':'function','function':{'name':'write_file','description':'Replace an allowed file with the supplied UTF-8 content.','parameters':{'type':'object','properties':{'path':{'type':'string'},'content':{'type':'string'}},'required':['path','content'],'additionalProperties':False}}},
    {'type':'function','function':{'name':'run_checks','description':'Compile and run the fixed public checks. No arguments or arbitrary shell commands.','parameters':{'type':'object','properties':{},'additionalProperties':False}}},
]


def dump(path, data):
    tmp=path.with_suffix(path.suffix+'.tmp'); tmp.write_text(json.dumps(data,indent=2)+'\n'); tmp.replace(path)


def fingerprint():
    h=hashlib.sha256()
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
            h.update(str(p.relative_to(ROOT)).encode()+b'\0'+p.read_bytes()+b'\0')
    return h.hexdigest()


def catalog(): return json.loads((ROOT/'suite.json').read_text())['tasks']


def toolchain():
    def which(name):
        p=shutil.which(name)
        if not p:raise RuntimeError('Missing tool: '+name)
        return str(Path(p).resolve())
    # Resolve rustup shims before confinement; their toolchain selection reads host state.
    rustc=subprocess.check_output(['rustup','which','rustc'],text=True).strip()
    cargo=subprocess.check_output(['rustup','which','cargo'],text=True).strip()
    # Invoke the node shim by name, then pin the runtime it selects. Resolving
    # a multicall shim directly can turn `node` into a different CLI (e.g. vp).
    node=subprocess.check_output(['node','-p','process.execPath'],text=True).strip()
    tools=dict(rustc=rustc,cargo=cargo,node=str(Path(node).resolve()),tsc=which('tsc'))
    versions={k:subprocess.check_output([v,'--version'],text=True,stderr=subprocess.STDOUT).strip() for k,v in tools.items()}
    return tools,versions


def policy(work, home, tools):
    """Constrain model-authored code, including compiler-time execution, on macOS."""
    if sys.platform!='darwin' or not Path('/usr/bin/sandbox-exec').exists():
        raise RuntimeError('This runner requires macOS Seatbelt; no unconfined fallback')
    allowed=[work.resolve(),home.resolve(),Path(tools['rustc']).parent.parent,Path(tools['node']).parent]
    terms=' '.join('(subpath '+json.dumps(str(p))+')' for p in allowed)
    lines=['(version 1)','(allow default)','(deny network*)']
    for root in ['/Users','/private/tmp','/private/var/folders']:
        lines.append('(deny file-read-data (require-all (subpath '+json.dumps(root)+') (require-not (require-any '+terms+'))))')
    writes=' '.join('(subpath '+json.dumps(str(p.resolve()))+')' for p in [work,home])
    lines.append('(deny file-write* (require-not (require-any '+writes+' (literal "/dev/null") (literal "/dev/urandom"))))')
    path=home/'sandbox.sb';path.write_text('\n'.join(lines));return path


def execute(argv, work, home, tools, timeout=45):
    home.mkdir(parents=True,exist_ok=True);(home/'tmp').mkdir(exist_ok=True)
    sb=policy(work,home,tools)
    env={'HOME':str(home),'CARGO_HOME':str(home/'cargo'),'RUSTUP_HOME':str(home/'rustup'),
         'PATH':os.pathsep.join([str(Path(tools['cargo']).parent),str(Path(tools['node']).parent),'/opt/homebrew/bin','/usr/bin','/bin']),
         'TMPDIR':str(home/'tmp'),'LANG':'en_US.UTF-8','CARGO_NET_OFFLINE':'true','XCRUN_CACHE_PATH':str(home/'xcrun-cache')}
    p=subprocess.run(['/usr/bin/sandbox-exec','-f',str(sb),*argv],cwd=work,env=env,capture_output=True,text=True,timeout=timeout)
    return {'returncode':p.returncode,'stdout':p.stdout[-16000:],'stderr':p.stderr[-16000:]}


def public_checks(task, work, home, tools):
    commands=([[tools['cargo'],'test','--offline','--all-targets']] if task['language']=='rust' else
              [[tools['tsc'],'-p','tsconfig.json'],[tools['node'],'--test','tests/public.mjs']])
    results=[]
    for argv in commands:
        r=execute(argv,work,home,tools);results.append({'argv':argv,**r})
        if r['returncode']:break
    return results


def checked_path(work, value):
    if not isinstance(value,str) or not value or Path(value).is_absolute():raise ValueError('Use a relative file path')
    path=(work/value).resolve()
    if not path.is_relative_to(work.resolve()):raise ValueError('Path outside workspace')
    return path


def dispatch(name, args, task, work, home, tools):
    if not isinstance(args,dict):raise ValueError('Arguments must be an object')
    if name=='read_file':
        if set(args)!={'path'}:raise ValueError('Expected path only')
        p=checked_path(work,args['path'])
        with p.open('rb') as f:return {'content':f.read(64000).decode('utf8',errors='replace')}
    if name=='write_file':
        if set(args)!={'path','content'}:raise ValueError('Expected path and content')
        p=checked_path(work,args['path']);relative=p.relative_to(work.resolve()).as_posix()
        if relative not in task['allowed_files']:raise ValueError('This file is protected: '+relative)
        content=args['content']
        if not isinstance(content,str) or len(content.encode())>128000:raise ValueError('Content must be a string of at most 128000 bytes')
        p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content);return {'written':relative}
    if name=='run_checks':
        if args:raise ValueError('run_checks takes no arguments')
        return {'checks':public_checks(task,work,home,tools)}
    raise ValueError('Unknown tool')


def agent(config, task, work, home, tools, evidence):
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':(ROOT/'tasks'/task['id']/'prompt.md').read_text()}]
    events=evidence/'events.jsonl'; state={'status':'running','requests':0,'tool_calls':0,'tool_errors':0,'usage':[]}
    def save():dump(evidence/'agent.json',state)
    save()
    for _ in range(config['max_requests']):
        payload={'model':config['model'],'messages':messages,'tools':TOOLS,'stream':False,'max_tokens':config['max_tokens'],
                 'temperature':config['temperature'],'top_p':config['top_p']}
        if config['top_k'] is not None:payload['top_k']=config['top_k']
        headers={'Content-Type':'application/json'}
        key=os.environ.get(config['api_key_env'],'')
        if key:headers['Authorization']='Bearer '+key
        request=urllib.request.Request(config['base_url'].rstrip('/')+'/chat/completions',json.dumps(payload).encode(),headers)
        with urllib.request.urlopen(request,timeout=config['timeout']) as response:result=json.load(response)
        choice=result['choices'][0]; raw=choice['message']
        message={k:v for k,v in raw.items() if k in ['role','content','tool_calls','reasoning_content']};message['role']='assistant'
        if 'reasoning_content' not in message and 'reasoning' in raw:
            message['reasoning_content']=raw['reasoning']
        messages.append(message);state['requests']+=1;state['usage'].append(result.get('usage',{}))
        with events.open('a') as f:f.write(json.dumps({'type':'response','choice':choice,'usage':result.get('usage',{})})+'\n')
        save()
        if choice.get('finish_reason')=='length':state['status']='output_limit';save();return
        calls=message.get('tool_calls') or []
        if not calls:state['status']='completed';save();return
        if len(calls)>config['max_tool_calls']-state['tool_calls']:state['status']='tool_limit';save();return
        for call in calls:
            state['tool_calls']+=1
            try: output=dispatch(call['function']['name'],json.loads(call['function']['arguments']),task,work,home,tools)
            except (ValueError,OSError) as e:output={'error':str(e)};state['tool_errors']+=1
            messages.append({'role':'tool','tool_call_id':call['id'],'content':json.dumps(output)})
            with events.open('a') as f:f.write(json.dumps({'type':'tool','name':call['function']['name'],'result':output})+'\n')
            save()
    state['status']='request_limit';save()


def worker(config, task, work, home, tools, evidence):
    os.setsid()
    try:agent(config,task,work,home,tools,evidence)
    except Exception as e:
        p=evidence/'agent.json';state=json.loads(p.read_text()) if p.exists() else {}
        state.update(status='infrastructure_error',error=type(e).__name__+': '+str(e));dump(p,state)


def protected_changes(task,work):
    changes=[]
    for p in work.rglob('*'):
        if p.is_symlink():changes.append('symlink: '+str(p.relative_to(work)))
    for p in (ROOT/'tasks'/task['id']/'seed').rglob('*'):
        if p.is_file():
            rel=p.relative_to(ROOT/'tasks'/task['id']/'seed')
            if str(rel) not in task['allowed_files']:
                q=work/rel
                if not q.is_file() or q.is_symlink() or q.read_bytes()!=p.read_bytes():changes.append(str(rel))
    return changes


def assess(task, work, evidence, tools):
    changed=protected_changes(task,work)
    if changed:return {'passed':False,'score':0,'error':'Protected files changed','paths':changed}
    with tempfile.TemporaryDirectory(prefix='small-eval-grade-',dir='/private/tmp') as td:
        base=Path(td)
        return grade(task,work,base/'work',tools,lambda argv,cwd:execute(argv,cwd,base/'home',tools),ROOT/'tasks'/task['id'])


def run_trial(config, task, evidence, tools):
    import multiprocessing
    evidence.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='small-eval-task-',dir='/private/tmp') as td:
        work=Path(td)/'work';home=Path(td)/'home';shutil.copytree(ROOT/'tasks'/task['id']/'seed',work)
        p=multiprocessing.get_context('spawn').Process(target=worker,args=(config,task,work,home,tools,evidence))
        started=time.monotonic();p.start();p.join(config['timeout']);timed_out=p.is_alive()
        if timed_out:
            try:os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            p.join(2)
        # Clean up compiler/test descendants even if the worker failed first.
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        p.join();elapsed=time.monotonic()-started
        state=json.loads((evidence/'agent.json').read_text()) if (evidence/'agent.json').exists() else {'status':'infrastructure_error','error':'worker exited without a checkpoint'}
        if state.get('status')=='running' and not timed_out:state.update(status='infrastructure_error',error='worker exited unexpectedly')
        if timed_out:state['status']='timeout';dump(evidence/'agent.json',state)
        shutil.copytree(work,evidence/'candidate',ignore=shutil.ignore_patterns('target','dist','.git'),symlinks=True)
        try:assessment=assess(task,work,evidence,tools)
        except Exception as e:assessment={'passed':False,'score':0,'infrastructure_error':type(e).__name__+': '+str(e)}
        result={'task':task['id'],'language':task['language'],'elapsed_seconds':elapsed,'agent':state,'assessment':assessment,
                'passed':state['status']=='completed' and assessment['passed'],
                'score':assessment['score'] if state['status']=='completed' else 0}
        dump(evidence/'result.json',result);return result


def verify():
    tools,versions=toolchain(); results=[]
    for task in catalog():
        with tempfile.TemporaryDirectory(prefix='small-eval-fixture-',dir='/private/tmp') as td:
            base=Path(td);work=base/'work';shutil.copytree(ROOT/'tasks'/task['id']/'seed',work)
            baseline=assess(task,work,base,tools)
            for p in (ROOT/'tasks'/task['id']/'reference').rglob('*'):
                if p.is_file():
                    dest=work/p.relative_to(ROOT/'tasks'/task['id']/'reference');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
            reference=assess(task,work,base,tools)
            item={'task':task['id'],'baseline_passed':baseline['passed'],'reference_passed':reference['passed']}
            if baseline['passed'] or not reference['passed']:
                print(json.dumps({'item':item,'baseline':baseline,'reference':reference},indent=2));raise RuntimeError('Fixture calibration failed')
            print(json.dumps(item));results.append(item)
    print(json.dumps({'toolchain':versions,'suite_sha256':fingerprint(),'fixtures':len(results)}))


def compare(paths):
    runs=[json.loads((Path(p)/'summary.json').read_text()) for p in paths]
    keys=['suite_sha256','toolchain','budget','sampling','tasks','system_prompt_sha256','requested_repeat']
    matched=all(all(runs[0][k]==r[k] for k in keys) for r in runs[1:])
    print('Matched protocol: '+str(matched))
    if not matched:print('Configurations differ; treat this as a setup comparison, not a controlled model comparison.')
    print('| Label | Finished/planned | Passed | Mean automatic score | Median seconds |')
    print('|---|---:|---:|---:|---:|')
    for r in runs:
        trials=r['results'];planned=len(r['tasks'])*r['requested_repeat'];score=sum(x['score'] for x in trials)/len(trials) if trials else 0
        score_text=f'{score:.2f}' if len(trials)==planned else 'incomplete'
        print(f"| {r['label']} | {len(trials)}/{planned} | {sum(x['passed'] for x in trials)} | {score_text} | {statistics.median(x['elapsed_seconds'] for x in trials) if trials else 0:.1f} |")
    for task in sorted({x['task'] for r in runs for x in r['results']}):
        print(task+': '+ '; '.join(r['label']+' '+str(sum(x['passed'] for x in r['results'] if x['task']==task))+'/'+str(sum(x['task']==task for x in r['results'])) for r in runs))


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('list');sub.add_parser('verify-fixtures')
    c=sub.add_parser('compare');c.add_argument('runs',nargs='+')
    run=sub.add_parser('run');run.add_argument('--label',required=True);run.add_argument('--base-url',required=True);run.add_argument('--model',required=True)
    run.add_argument('--api-key-env',default='LOCAL_EVAL_API_KEY');run.add_argument('--tasks',default='all');run.add_argument('--repeat',type=int,default=1)
    run.add_argument('--timeout',type=int,default=180);run.add_argument('--max-requests',type=int,default=24);run.add_argument('--max-tool-calls',type=int,default=40)
    run.add_argument('--max-tokens',type=int,default=32768);run.add_argument('--temperature',type=float,default=1.0);run.add_argument('--top-p',type=float,default=.95);run.add_argument('--top-k',type=int)
    run.add_argument('--output',type=Path);run.add_argument('--runtime-info',type=Path,help='JSON metadata: runtime, runtime_version, model_revision, quantization, context_window, speculation')
    args=parser.parse_args()
    if args.command=='list':
        for t in catalog():print(t['id'],t['language'],t['kind'])
        return
    if args.command=='verify-fixtures':verify();return
    if args.command=='compare':compare(args.runs);return
    if any(getattr(args,k)<=0 for k in ['repeat','timeout','max_requests','max_tool_calls','max_tokens']):parser.error('Budgets must be positive')
    url=urllib.parse.urlsplit(args.base_url)
    if url.scheme not in ['http','https'] or not url.hostname or url.username or url.password or url.query or url.fragment:parser.error('Use an HTTP(S) base URL without credentials/query/fragment')
    tasks=catalog() if args.tasks=='all' else [t for t in catalog() if t['id'] in args.tasks.split(',')]
    if not tasks or args.tasks!='all' and set(args.tasks.split(','))!={t['id'] for t in tasks}:parser.error('Unknown task selection')
    tools,versions=toolchain();config=vars(args).copy();config.pop('output');config.pop('command');config.pop('runtime_info')
    output=args.output or DEFAULT_RUNS/(time.strftime('%Y%m%d-%H%M%S')+'-'+''.join(c if c.isalnum() or c in '-_' else '_' for c in args.label))
    runtime_info=json.loads(args.runtime_info.read_text()) if args.runtime_info else {}
    allowed={'runtime','runtime_version','model_revision','quantization','context_window','speculation'}
    if not isinstance(runtime_info,dict) or set(runtime_info)-allowed:parser.error('Unsupported runtime metadata field; never include credentials')
    output=output.resolve()
    if output.is_relative_to(ROOT):parser.error('Store run evidence outside the suite source directory')
    output.mkdir(parents=True,exist_ok=False)
    summary={'label':args.label,'model':args.model,'base_url':args.base_url,'suite_sha256':fingerprint(),'system_prompt_sha256':hashlib.sha256(SYSTEM.encode()).hexdigest(),
             'toolchain':versions,'budget':{k:config[k] for k in ['timeout','max_requests','max_tool_calls','max_tokens']},'sampling':{k:config[k] for k in ['temperature','top_p','top_k']},
             'tasks':[t['id'] for t in tasks],'results':[],'requested_repeat':args.repeat,'runtime_info':runtime_info}
    dump(output/'summary.json',summary);print('Results: '+str(output),flush=True)
    for repeat in range(args.repeat):
        for task in tasks:
            result=run_trial(config,task,output/f"{repeat+1:02d}-{task['id']}",tools)
            summary['results'].append(result);dump(output/'summary.json',summary)
            print(task['id'],result['agent']['status'],'score',result['score'],f"{result['elapsed_seconds']:.1f}s",flush=True)
            if result['agent']['status'] in ['timeout','infrastructure_error']:
                print('Stopped suite: check endpoint health/cancellation before resuming. No server was stopped.');return
    print('Finished. Prose clarity still requires manual review.')

if __name__=='__main__':main()
