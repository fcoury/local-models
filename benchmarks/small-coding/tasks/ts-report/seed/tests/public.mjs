import {test} from 'node:test';
import assert from 'node:assert/strict';
import {summarizeJsonLines} from '../dist/index.js';
test('groups',()=>assert.deepEqual(summarizeJsonLines('{"account":"a","cents":3}\n{"account":"a","cents":-1}'),[{account:'a',totalCents:2,count:2}]));
