"""Independent task checks. The model never receives this module or its tests."""
import json
import re
import shutil
from pathlib import Path

RUST_CHECKS = {
    'rust-utf8': r'''
use task::truncate_utf8;
use std::alloc::{GlobalAlloc,Layout,System};
use std::cell::Cell;
thread_local! { static TRACK: Cell<bool> = const { Cell::new(false) }; static ALLOCS: Cell<usize> = const { Cell::new(0) }; }
struct Tracking;
unsafe impl GlobalAlloc for Tracking {
 unsafe fn alloc(&self,l:Layout)->*mut u8 {
  if TRACK.try_with(|v|v.get()).unwrap_or(false) { let _=ALLOCS.try_with(|v|v.set(v.get()+1)); }
  unsafe { System.alloc(l) }
 }
 unsafe fn dealloc(&self,p:*mut u8,l:Layout) { unsafe { System.dealloc(p,l) } }
 unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8 {
  if TRACK.try_with(|v|v.get()).unwrap_or(false) { let _=ALLOCS.try_with(|v|v.set(v.get()+1)); }
  unsafe { System.realloc(p,l,n) }
 }
}
#[global_allocator] static ALLOCATOR:Tracking=Tracking;
#[test] fn no_allocations() {
 let s=String::from("helloé🦀world");
 for n in 0..s.len()+2 {
  ALLOCS.with(|v|v.set(0)); TRACK.with(|v|v.set(true));
  let out=truncate_utf8(&s,n);
  TRACK.with(|v|v.set(false));
  assert_eq!(ALLOCS.with(|v|v.get()),0,"allocation at limit {n}"); assert_eq!(out.as_ptr(),s.as_ptr());
 }
}
#[test] fn unicode_and_boundaries() {
 let samples=["", "abc", "éclair", "a🦀b", "你好", "e\u{301}x", "\0x"];
 for s in samples { for limit in (0..s.len()+3).chain([usize::MAX]) {
  let expected: String=s.chars().scan(0usize,|used,ch| { *used+=ch.len_utf8(); Some((*used,ch)) }).take_while(|(n,_)| *n<=limit).map(|(_,c)|c).collect();
  let out=truncate_utf8(s,limit); assert_eq!(out,expected,"input={s:?} limit={limit}"); assert_eq!(out.as_ptr(),s.as_ptr());
 }}
}
#[test] fn generated_inputs() {
 let chars=['a','é','🦀','中','\u{301}']; let mut state=17u32;
 for _ in 0..100 { let mut s=String::new(); for _ in 0..12 { state=state.wrapping_mul(1664525).wrapping_add(1013904223); s.push(chars[state as usize%chars.len()]); }
 for n in 0..s.len()+1 { let out=truncate_utf8(&s,n); assert!(s.starts_with(out)); assert!(out.len()<=n); assert!(out.len()==s.len() || out.len()+s[out.len()..].chars().next().unwrap().len_utf8()>n); }
 }
}
''',
    'rust-migrate': r'''
use task::{normalize_tag,TagError,service::render_tags};
#[test] fn normalization() {
 for (s,e) in [(" A_B-c9 ","a_b-c9"),("Z","z"),("000","000")] { assert_eq!(normalize_tag(s),Ok(e.into())); }
 for s in ["", " \t\n"] { assert_eq!(normalize_tag(s),Err(TagError::Empty)); }
 for s in ["a b","é","a.b","a/b","🦀","a\0b"] { assert_eq!(normalize_tag(s),Err(TagError::InvalidCharacter)); }
}
#[test] fn callers_propagate_and_preserve() {
 assert_eq!(render_tags(&[]),Ok(String::new())); assert_eq!(render_tags(&[" A ","a","B_2"]),Ok("a,a,b_2".into()));
 assert_eq!(render_tags(&["ok","", "a b"]),Err(TagError::Empty)); assert_eq!(render_tags(&["a b", ""]),Err(TagError::InvalidCharacter));
}
''',
}
TS_CHECKS = {
    'ts-money': r'''
import assert from 'node:assert/strict';
import {parseCents} from './dist/index.js';
for(const [s,v] of [['0',0],['-0',0],['-0.00',0],['001.2',120],['0.29',29],['-1.01',-101],['90071992547409.91',Number.MAX_SAFE_INTEGER],['-90071992547409.91',-Number.MAX_SAFE_INTEGER]]) assert.equal(parseCents(s),v,s);
for(const s of ['', ' ', '+1','1e2','1.001','.1','1.',' 1','1 ', '1\n','１２','NaN','Infinity','--1','90071992547409.92','-90071992547409.92','99999999999999999999999']) assert.equal(parseCents(s),null,JSON.stringify(s));
for(let n=-300;n<=300;n++){ const s=(n<0?'-':'')+Math.floor(Math.abs(n)/100)+'.'+String(Math.abs(n)%100).padStart(2,'0'); assert.equal(parseCents(s),n===0?0:n); }
console.log('ACCEPTANCE_OK');
''',
    'ts-report': r'''
import assert from 'node:assert/strict';
import {summarizeJsonLines as f} from './dist/index.js';
assert.deepEqual(f(' \n\r\n'),[]);
const rows=[{account:' b ',cents:3},{account:'a',cents:2},{account:'b',cents:-3},{account:'__proto__',cents:0},{account:'a',cents:4,other:true},{account:'A',cents:1}];
assert.deepEqual(f(rows.map(JSON.stringify).join('\r\n')),[{account:'A',totalCents:1,count:1},{account:'__proto__',totalCents:0,count:1},{account:'a',totalCents:6,count:2},{account:'b',totalCents:0,count:2}]);
for(const row of [null,[],1,{account:' ',cents:1},{account:7,cents:1},{account:'a',cents:'1'},{account:'a',cents:0.1},{account:'a',cents:Number.MAX_SAFE_INTEGER+1},{account:'a'}]) assert.throws(()=>f(JSON.stringify(row)),Error);
assert.throws(()=>f('{oops'),Error);
assert.throws(()=>f(JSON.stringify({account:'a',cents:Number.MAX_SAFE_INTEGER})+'\n'+JSON.stringify({account:'a',cents:1})),Error);
assert.throws(()=>f('{"account":"a","cents":1}\nnull'),Error);
console.log('ACCEPTANCE_OK');
''',
}
FACTS = dict(accepted=[True, True, False, True, True], retained=[10, 11],
             eviction_age_at_least_window=True, rejected_requests_recorded=False,
             worst_case='O(n)', amortized='O(1)')


def passed_rust(result):
    match = re.search(r'test result: ok\. (\d+) passed;', result['stdout'])
    return result['returncode'] == 0 and bool(match) and int(match[1]) > 0


def grade(task, candidate, destination, tools, execute, task_root):
    """execute runs argv in the confined verifier directory, with a deadline."""
    shutil.copytree(candidate, destination, ignore=shutil.ignore_patterns('target', 'dist', '.git'))
    work = destination
    logs = []
    def call(argv):
        result = execute(argv, work)
        logs.append({'argv': argv, **result})
        return result
    def library(source=None):
        if source is not None:
            (work/'src/lib.rs').write_text(source)
        return call([tools['rustc'], '--edition=2024', '--crate-name', 'task', '--crate-type', 'rlib', 'src/lib.rs', '-o', 'libtask.rlib'])['returncode'] == 0
    if task['kind'] == 'explanation':
        try:
            answer = json.loads((work/'answer.json').read_text())
            prose = (work/'EXPLANATION.md').read_text()
            if not isinstance(answer, dict) or set(answer) != set(FACTS) or not 1 <= len(prose.split()) <= 250:
                raise ValueError('Wrong answer shape or missing/overlong prose')
            correct = sum(json.dumps(answer[k],sort_keys=True) == json.dumps(v,sort_keys=True) for k,v in FACTS.items())
            return {'score':correct/len(FACTS),'passed':correct==len(FACTS),'facts_correct':correct,'facts_total':len(FACTS),'prose_review':'manual; not automatically scored','logs':logs}
        except (OSError,ValueError) as e:
            return {'score':0,'passed':False,'error':str(e),'logs':logs}
    if task['kind'] == 'mutation':
        tests = work/'tests/ports.rs'
        if not tests.is_file():return {'score':0,'passed':False,'error':'No submitted tests','logs':logs}
        def check(source):
            if not library(source):return False
            built=call([tools['rustc'],'--edition=2024','--test','tests/ports.rs','--extern','task=libtask.rlib','-o','ports-test'])
            return built['returncode']==0 and passed_rust(call([str(work/'ports-test')]))
        correct_source=(task_root/'seed/src/lib.rs').read_text()
        if not check(correct_source):return {'score':0,'passed':False,'error':'Tests do not pass on the correct implementation','logs':logs}
        killed=[]; survived=[]
        for mutant in sorted((task_root/'mutants').glob('*.rs')):
            (survived if check(mutant.read_text()) else killed).append(mutant.stem)
        return {'score':len(killed)/(len(killed)+len(survived)),'passed':not survived,'mutants_killed':killed,'mutants_survived':survived,'logs':logs}
    if task['language']=='rust':
        if not library():return {'score':0,'passed':False,'logs':logs}
        (work/'acceptance.rs').write_text(RUST_CHECKS[task['id']])
        built=call([tools['rustc'],'--edition=2024','--test','acceptance.rs','--extern','task=libtask.rlib','-o','acceptance'])
        ok=built['returncode']==0 and passed_rust(call([str(work/'acceptance')]))
    else:
        built=call([tools['tsc'],'-p','tsconfig.json'])
        (work/'acceptance.mjs').write_text(TS_CHECKS[task['id']])
        result=call([tools['node'],'acceptance.mjs']) if built['returncode']==0 else {'returncode':1,'stdout':''}
        ok=result['returncode']==0 and 'ACCEPTANCE_OK' in result['stdout'].splitlines()
    return {'score':int(ok),'passed':ok,'logs':logs}
