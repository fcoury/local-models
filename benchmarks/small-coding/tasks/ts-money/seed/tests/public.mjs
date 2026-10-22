import {test} from 'node:test';
import assert from 'node:assert/strict';
import {parseCents} from '../dist/index.js';
test('decimal',()=>assert.equal(parseCents('12.30'),1230));
test('no exponent',()=>assert.equal(parseCents('1e2'),null));
