"""Run the qualified Inkling low-effort five-task deployment and independently grade."""
import argparse,json,subprocess,sys,time,threading,urllib.request
from pathlib import Path
from aider_host import save,run_benchmark,independent_grade
from compare_aider import digest,get,monitor,verify
from types import SimpleNamespace
from bounded import stop_group

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
 protocol=json.loads((Path(__file__).parent/'inkling-protocol.json').read_text())
 root=a.root; run=root/'inkling-low';run.mkdir(exist_ok=False)
 for file,sha in protocol['frozen_files'].items():
  assert digest(Path(__file__).parent/file)==sha,file
 verify(SimpleNamespace(prepared=root/'prepared',modelctl=Path('/Users/fcoury/code/local-models/bin/modelctl')),protocol)
 receipt=json.loads((root/'artifact-verification.json').read_text());assert receipt['verified']
 model=Path(receipt['path']);assert model.stat().st_size==receipt['bytes'] and model.stat().st_mtime_ns==receipt['mtime_ns']
 binary=Path(protocol['binary']);assert digest(binary)==protocol['binary_sha256']
 for port in [18490,18436]:
  assert subprocess.run(['lsof','-nP',f'-iTCP:{port}','-sTCP:LISTEN'],capture_output=True).returncode==1
 argv=[str(binary),'-m',str(model),'--host','127.0.0.1','--port','18436','--alias','inkling-mini-q8','-c','65536','-np','1','-ngl','99','--jinja','--reasoning-effort','low','--reasoning-format','deepseek','--no-context-shift']
 save(run/'protocol.json',protocol);save(run/'argv.json',argv)
 server=policy=None; stopped=threading.Event();worker=None
 try:
  with (run/'server.log').open('w') as log,(run/'policy.log').open('w') as plog:
   server=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   save(run/'owner.json',{'pid':server.pid})
   for _ in range(600):
    if server.poll() is not None: raise RuntimeError('Server exited')
    try: get('http://127.0.0.1:18436/health');break
    except OSError:time.sleep(1)
   else:raise RuntimeError('Load timeout')
   save(run/'props.json',get('http://127.0.0.1:18436/props'))
   policy=subprocess.Popen([sys.executable,str(Path(__file__).parent/'api_policy.py'),'--upstream','http://127.0.0.1:18436/v1','--model','inkling-mini-q8','--backend','inkling','--audit',str(run/'request-controls.jsonl')],stdout=plog,stderr=subprocess.STDOUT,start_new_session=True)
   for _ in range(100):
    try:get('http://127.0.0.1:18490/v1/models');break
    except OSError:time.sleep(.1)
   req=urllib.request.Request('http://127.0.0.1:18490/v1/chat/completions',data=json.dumps({'model':'rust-eval','messages':[{'role':'user','content':'Reply exactly READY'}],'max_tokens':512}).encode(),headers={'Content-Type':'application/json'})
   with urllib.request.urlopen(req,timeout=600) as response:smoke=json.load(response)
   save(run/'smoke.json',smoke);assert 'READY' in (smoke['choices'][0]['message'].get('content') or '')
   # A forced function call must survive parsing with structured arguments.
   body={'model':'inkling-mini-q8','messages':[{'role':'user','content':'Call add with a=2 and b=3.'}],'tools':[{'type':'function','function':{'name':'add','parameters':{'type':'object','properties':{'a':{'type':'integer'},'b':{'type':'integer'}},'required':['a','b']}}}],'tool_choice':{'type':'function','function':{'name':'add'}},'reasoning_effort':'low','temperature':0,'max_tokens':512}
   req=urllib.request.Request('http://127.0.0.1:18436/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
   with urllib.request.urlopen(req,timeout=600) as response:tool=json.load(response)
   save(run/'tool-smoke.json',tool)
   call=tool['choices'][0]['message']['tool_calls'][0]['function'];assert call['name']=='add' and json.loads(call['arguments'])=={'a':2,'b':3}
   worker=threading.Thread(target=monitor,args=(run,server.pid,'http://127.0.0.1:18436/v1',stopped),daemon=True);worker.start()
   timing,name,records=run_benchmark(protocol['image'],root/'prepared',run,protocol['exercises'],3600)
   save(run/'generation.json',{'timing':timing,'name':name,'records':records})
 finally:
  if policy is not None:stop_group(policy)
  stopped.set()
  if worker:worker.join(timeout=10)
  if server is not None:stop_group(server)
  save(run/'shutdown.json',{'server_returncode':server.returncode if server else None})
 manifest,grades=independent_grade(protocol['image'],root/'prepared',run)
 verified={(g['exercise'],g['attempt']):g['passed'] for g in grades}
 for r in records:assert [verified[r['testcase'],i+1] for i in range(len(r['tests_outcomes']))]==r['tests_outcomes']
 save(run/'result.json',{'first_try':sum(r['tests_outcomes'][0] for r in records),'within_two':sum(any(r['tests_outcomes']) for r in records),'denominator':5,'independently_verified':True,'timing':timing})
 print((run/'result.json').read_text(),flush=True)
if __name__=='__main__':main()
