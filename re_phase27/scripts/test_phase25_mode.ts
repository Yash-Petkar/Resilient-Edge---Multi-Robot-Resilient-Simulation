import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import { resolveDemoMode } from '../src/config/demoMode';

assert.equal(resolveDemoMode('true'), true);
assert.equal(resolveDemoMode('TRUE'), true);
assert.equal(resolveDemoMode(' false '), false);
assert.equal(resolveDemoMode(false), false);
assert.equal(resolveDemoMode(undefined), false);

const apiServiceSource = readFileSync('src/services/apiService.ts', 'utf8');
const appSource = readFileSync('src/App.tsx', 'utf8');
const serverSource = readFileSync('server.ts', 'utf8');

assert.match(apiServiceSource, /import\.meta\.env\.VITE_DEMO_MODE/);
assert.doesNotMatch(apiServiceSource, /isDemoMode\(\)[\s\S]*return true;/);
assert.doesNotMatch(appSource, /<PreLoginExperience demoMode /);
assert.match(appSource, /demoMode=\{demoMode\}/);
assert.doesNotMatch(serverSource, /DEMO_MODE:\s*['"]true['"]/);

console.log('Phase 25 frontend mode tests: PASS');
