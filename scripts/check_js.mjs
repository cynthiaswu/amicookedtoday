// Fails CI if the inline script has a syntax error. Catches the classic
// "</script> inside a JS comment" trap, which silently truncates the app.
import { readFileSync, writeFileSync, unlinkSync } from 'fs';
import { execSync } from 'child_process';

const html = readFileSync('index.html', 'utf8');
const blocks = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)];
if (!blocks.length) { console.error('FAIL: no inline script found'); process.exit(1); }

let bad = 0;

// A literal </script> anywhere in the JS — even inside a comment or string —
// terminates the block early. The browser does not care that it's a comment.
// The truncated remainder can still parse cleanly, so a syntax check alone
// misses this. Catch it structurally instead.
const opens  = (html.match(/<script\b/g)  || []).length;
const closes = (html.match(/<\/script>/g) || []).length;
if (opens !== closes) {
  console.error(`  FAIL  unbalanced script tags: ${opens} open, ${closes} close`);
  bad++;
}
blocks.forEach((m, i) => {
  if (/<script\b|<\/script/.test(m[1])) {
    console.error(`  FAIL  script block ${i} contains a literal script tag — it will truncate here`);
    bad++;
  }
});
blocks.forEach((m, i) => {
  const tmp = `.check_${i}.mjs`;
  writeFileSync(tmp, m[1]);
  try { execSync(`node --check ${tmp}`, { stdio: 'pipe' }); console.log(`  PASS  script block ${i} (${m[1].split('\n').length} lines)`); }
  catch (e) { console.error(`  FAIL  script block ${i}\n${e.stderr?.toString() ?? e}`); bad++; }
  finally { unlinkSync(tmp); }
});
process.exit(bad ? 1 : 0);
