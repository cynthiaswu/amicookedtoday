// The sky shader fails at runtime, not build time — a bad edit ships as a blank
// background on some GPUs and nothing else. Parse it in CI instead.
import { readFileSync } from 'fs';
import { createRequire } from 'module';
// the parser ships CommonJS — a named ESM import throws at load
const { parse } = createRequire(import.meta.url)('@shaderfrog/glsl-parser');

const html = readFileSync('index.html', 'utf8');
const m = html.match(/const FS = `([\s\S]*?)`;/);
if (!m) { console.error('FAIL: fragment shader not found'); process.exit(1); }
const src = m[1];

try { parse(src); console.log(`  PASS  GLSL parses (${src.split('\n').length} lines)`); }
catch (e) { console.error('  FAIL  GLSL syntax:', e.message); process.exit(1); }

// GLSL ES 1.0 rules the parser doesn't enforce
const rules = [
  ['precision declared',        /precision\s+\w+\s+float/.test(src)],
  ['writes gl_FragColor',       /gl_FragColor\s*=/.test(src)],
  ['loops have constant bounds', !/for\s*\([^)]*<\s*[a-zA-Z_]/.test(src)],
  ['no ES3-only "in/out" quals', !/^\s*(in|out)\s+(vec|float|int)/m.test(src)],
];
let bad = 0;
for (const [n, ok] of rules) { console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}`); if (!ok) bad++; }
process.exit(bad ? 1 : 0);
