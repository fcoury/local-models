#!/usr/bin/env python3
"""Offline integration checks: no model, provider key, or download required."""
import contextlib
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT=Path(__file__).resolve().parents[1]/'benchmarks/small-coding'
sys.path.insert(0,str(ROOT))
evalmod=importlib.import_module('eval')


class Endpoint(BaseHTTPRequestHandler):
    requests=[]
    mode='solve'
    def log_message(self,*args):pass
    def do_POST(self):
        payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        Endpoint.requests.append(payload)
        if Endpoint.mode=='slow':time.sleep(3)
        count=sum(m.get('role')=='tool' for m in payload['messages'])
        if count<3:
            name,args=[('read_file',{'path':'src/lib.rs'}),
                       ('write_file',{'path':'src/lib.rs','content':(ROOT/'tasks/rust-utf8/reference/src/lib.rs').read_text()}),
                       ('run_checks',{})][count]
            message={'role':'assistant','content':None,'reasoning':'retained reasoning',
                     'tool_calls':[{'id':str(count),'type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}
            finish='tool_calls'
        else:message={'role':'assistant','content':'Fixed and tested.'};finish='stop'
        response=json.dumps({'choices':[{'message':message,'finish_reason':finish}],'usage':{'prompt_tokens':20,'completion_tokens':10}}).encode()
        try:
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(response)));self.end_headers();self.wfile.write(response)
        except BrokenPipeError:pass


class EvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tools,_=evalmod.toolchain()
    def config(self,port,timeout=30):
        return dict(model='scripted',base_url=f'http://127.0.0.1:{port}/v1',api_key_env='SMALL_EVAL_TEST_NO_KEY',timeout=timeout,max_requests=8,max_tool_calls=8,max_tokens=32768,temperature=1.0,top_p=.95,top_k=20)
    def task(self):return next(t for t in evalmod.catalog() if t['id']=='rust-utf8')
    def test_resolved_node_executes_javascript_in_sandbox(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as td:
            work=Path(td)/'work';work.mkdir()
            result=evalmod.execute([self.tools['node'],'-p','6 * 7'],work,Path(td)/'home',self.tools)
            self.assertEqual(result['returncode'],0,result)
            self.assertEqual(result['stdout'].strip(),'42')
    def endpoint(self,mode):
        Endpoint.mode=mode;Endpoint.requests=[]
        server=ThreadingHTTPServer(('127.0.0.1',0),Endpoint);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();self.addCleanup(server.server_close);self.addCleanup(server.shutdown);return server
    def test_real_tool_loop_and_independent_grading(self):
        server=self.endpoint('solve')
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'trial';r=evalmod.run_trial(self.config(server.server_port),self.task(),out,self.tools)
            self.assertTrue(r['passed'],r);self.assertEqual(r['agent']['tool_calls'],3)
            self.assertEqual(Endpoint.requests[-1]['messages'][2]['reasoning_content'],'retained reasoning')
            self.assertEqual(Endpoint.requests[0]['top_k'],20)
            self.assertNotIn('acceptance',json.dumps(Endpoint.requests))
    def test_deadline_does_not_pass_an_unfinished_trial(self):
        server=self.endpoint('slow')
        with tempfile.TemporaryDirectory() as td:
            start=time.monotonic();r=evalmod.run_trial(self.config(server.server_port,1),self.task(),Path(td)/'trial',self.tools)
            self.assertFalse(r['passed']);self.assertEqual(r['score'],0)
            self.assertIn(r['agent']['status'],['timeout','infrastructure_error']);self.assertLess(time.monotonic()-start,8)
    def test_correct_output_with_allocation_fails_rust_contract(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            work=Path(td)/'work';shutil.copytree(ROOT/'tasks/rust-utf8/seed',work)
            source=(ROOT/'tasks/rust-utf8/reference/src/lib.rs').read_text()
            source=source.replace('{','{ let allocated=input.as_bytes().to_vec(); std::hint::black_box(&allocated);',1)
            (work/'src/lib.rs').write_text(source)
            result=evalmod.assess(self.task(),work,Path(td),self.tools)
            self.assertFalse(result['passed'],result)
            self.assertIn('allocation at limit',json.dumps(result))
    def test_file_tools_cannot_escape_or_change_tests(self):
        with tempfile.TemporaryDirectory() as td:
            work=Path(td)/'work';work.mkdir();home=Path(td)/'home'
            for args in [{'path':'../answer','content':'x'},{'path':'tests/public.rs','content':'x'}]:
                with self.assertRaises(ValueError):evalmod.dispatch('write_file',args,self.task(),work,home,self.tools)
            (work/'escape').symlink_to(ROOT/'grading.py')
            with self.assertRaises(ValueError):evalmod.dispatch('read_file',{'path':'escape'},self.task(),work,home,self.tools)
    def test_seatbelt_denies_reference_reads_and_external_writes(self):
        with tempfile.TemporaryDirectory(prefix='small-eval-test-',dir='/private/tmp') as td:
            base=Path(td);work=base/'work';work.mkdir();home=base/'home';outside=base/'outside';outside.write_text('secret')
            r=evalmod.execute(['/bin/cat',str(outside)],work,home,self.tools)
            self.assertNotEqual(r['returncode'],0);self.assertNotIn('secret',r['stdout'])
            r=evalmod.execute(['/usr/bin/touch',str(base/'forbidden')],work,home,self.tools)
            self.assertNotEqual(r['returncode'],0);self.assertFalse((base/'forbidden').exists())
    def test_compare_detects_different_budgets(self):
        with tempfile.TemporaryDirectory() as td:
            dirs=[]
            for i in [1,2]:
                p=Path(td)/str(i);p.mkdir();dirs.append(p)
                evalmod.dump(p/'summary.json',dict(label=str(i),suite_sha256='same',toolchain={},budget={'timeout':i},sampling={},tasks=[],system_prompt_sha256='same',results=[],requested_repeat=1))
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):evalmod.compare(dirs)
            self.assertIn('Matched protocol: False',buf.getvalue())

if __name__=='__main__':unittest.main()
