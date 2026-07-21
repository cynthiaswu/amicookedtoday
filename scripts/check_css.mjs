// CSS stacking guard.
//
// The search dropdown lives inside the masthead <header>. The cards use
// backdrop-filter, which paints over absolutely-positioned siblings, so the
// dropdown only clears them if the WHOLE header is lifted above <main>.
//
// The trap that bit us three times: the base rule `body > *:not(#sky)` scores
// an ID (from #sky inside :not) — specificity (1,0,1). A plain `body > header`
// override is only (0,0,2) and SILENTLY LOSES, leaving the header at z-index:2,
// level with the cards. Nothing throws; the dropdown just hides.
//
// This check computes real specificity and fails if the header's z-index rule
// doesn't actually out-rank the base rule. It verifies the fix WORKS, not that
// a particular string is present — so a future refactor can't slip past it.

import { readFileSync } from 'fs';

const raw = readFileSync('index.html', 'utf8');
const css = raw.replace(/\/\*[\s\S]*?\*\//g, '');   // strip CSS comments so they can't pollute selector matches

// --- tiny specificity calculator (enough for the selectors we use) ----------
// returns [a,b,c] = [IDs, classes/attrs/pseudo-classes, types/pseudo-elements]
function specificity(sel) {
  let a = 0, b = 0, c = 0;
  // IDs inside :not(...) still count toward (a)
  const notIds = (sel.match(/:not\([^)]*#[\w-]+[^)]*\)/g) || []).length;
  // top-level IDs (# not immediately preceded by "not(")
  const bareIds = (sel.match(/#[\w-]+/g) || []).length;
  a = bareIds; // notIds are a subset of bareIds via the # match, so count once
  void notIds;
  b += (sel.match(/\.[\w-]+/g) || []).length;        // classes
  b += (sel.match(/\[[^\]]+\]/g) || []).length;       // attributes
  // pseudo-classes, but NOT the :not() wrapper itself (its contents are counted separately)
  b += (sel.match(/:(?!not\()[\w-]+/g) || []).length;
  c += (sel.match(/\b(?:body|header|main|footer|div|search|section|article|figure|nav|ul|li|a|p|span|input|button|canvas|svg)\b/g) || []).length;
  return [a, b, c];
}

function cmp(x, y) {           // +1 if x wins, -1 if y wins, 0 tie (source order)
  for (let i = 0; i < 3; i++) if (x[i] !== y[i]) return x[i] > y[i] ? 1 : -1;
  return 0;
}

// --- pull the rules we care about out of the stylesheet ---------------------
// base rule that sets the sibling stacking floor
const baseMatch = css.match(/body\s*>\s*\*:not\(#sky\)\s*\{[^}]*z-index\s*:\s*(\d+)/);
// the header override (however it's written)
const headMatch = css.match(/(?:^|\n)\s*(body\s*>\s*header[^{\n]*)\{[^}]*z-index\s*:\s*(\d+)/);

let failures = [];

if (!baseMatch) {
  failures.push('could not find the base `body > *:not(#sky)` z-index rule — did the stacking model change?');
} else if (!headMatch) {
  failures.push('no `body > header ...` z-index rule found — the masthead lift is missing, dropdown will hide behind cards');
} else {
  const baseSel = 'body > *:not(#sky)';
  const baseZ = +baseMatch[1];
  const headSel = headMatch[1].trim();
  const headZ = +headMatch[2];

  const baseSpec = specificity(baseSel);
  const headSpec = specificity(headSel);
  const winner = cmp(headSpec, baseSpec);

  console.log(`  base : ${baseSel}  (${baseSpec})  z-index:${baseZ}`);
  console.log(`  head : ${headSel}  (${headSpec})  z-index:${headZ}`);

  // the header rule must WIN the cascade (or tie with later source order) AND set a higher z
  if (winner < 0) {
    failures.push(
      `header rule (${headSpec}) loses on specificity to the base rule (${baseSpec}), ` +
      `so its z-index is ignored and the header stays at z-index:${baseZ}. ` +
      `Use \`body > header:not(#sky)\` to match the base rule's ID score.`
    );
  } else if (headZ <= baseZ) {
    failures.push(`header z-index (${headZ}) is not above the base stacking floor (${baseZ})`);
  }
}

// --- report -----------------------------------------------------------------
if (failures.length) {
  console.error('\n  FAIL  dropdown stacking:');
  for (const f of failures) console.error('   - ' + f);
  process.exit(1);
}
console.log('  PASS  masthead out-specifies the base rule; search dropdown clears the cards');
