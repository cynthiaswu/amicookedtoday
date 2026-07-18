#!/usr/bin/env python3
"""
WCAG contrast gate.

This site draws its own background, so the page can't be checked against a
static colour — the card sits on a live shader whose output ranges from a near
black night sky to a sunlit cloud. A palette edit that looks fine at noon can
be unreadable at dusk, and nothing throws.

So: reconstruct the shader's sky across every solar elevation, composite the
real card tokens over it, and assert AA. Colours are parsed out of index.html,
not hardcoded here — change a token and this test sees it.
"""
import re, sys

HTML = open('index.html').read()

# ---------- colour maths ----------------------------------------------------
def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def lum(rgb):
    return 0.2126*_lin(rgb[0]) + 0.7152*_lin(rgb[1]) + 0.0722*_lin(rgb[2])

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

def over(fg, bg, a):
    return tuple(fg[i]*a + bg[i]*(1-a) for i in range(3))

def hx(h):
    h = h.strip().lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t*t*(3 - 2*t)

def mix(a, b, t):
    return tuple(a[i] + (b[i]-a[i])*t for i in range(3))

# ---------- pull the real tokens out of the file ----------------------------
def css_var(name, scope=None):
    block = HTML
    if scope:
        m = re.search(re.escape(scope) + r'\{(.*?)\n  \}', HTML, re.S)
        if not m:
            sys.exit(f'FAIL: scope {scope} not found')
        block = m.group(1)
    m = re.search(rf'--{name}\s*:\s*(#[0-9A-Fa-f]{{6}})', block)
    if not m:
        sys.exit(f'FAIL: --{name} not found in {scope or ":root"}')
    return m.group(1)

def band_colours(key):
    return re.findall(rf"{key}\s*:\s*'(#[0-9A-Fa-f]{{6}})'", HTML)

LIGHT = {
    'ink':   css_var('ink'),
    'dim':   css_var('dim'),
    'muted': css_var('muted'),
    'good':  css_var('good'),
    'burn':  css_var('burn'),
}
NIGHT_SCOPE = '[data-sky="night"]'
NIGHT = {
    'ink':   css_var('ink',   NIGHT_SCOPE),
    'dim':   css_var('dim',   NIGHT_SCOPE),
    'muted': css_var('muted', NIGHT_SCOPE),
    'good':  css_var('good',  NIGHT_SCOPE),
    'burn':  css_var('burn',  NIGHT_SCOPE),
}
BAND_INK    = band_colours('ink')    # text-safe, used on light glass
BAND_BRIGHT = band_colours('col')    # graphic, used on dark glass + the sky

# adaptive glass: mirror the constants in applySkyTheme()
def glass_alpha(mu):
    return (0.66 + (0.34-0.66)*smoothstep(0.08, -0.14, mu) if mu < 0.08
            else 0.63 + (0.48-0.63)*smoothstep(0.08, 0.38, mu))

LIGHT_GLASS = (255, 255, 255)
DARK_GLASS  = (10, 8, 14)

# ---------- reconstruct the shader's sky ------------------------------------
def skies(mu):
    """Every colour the shader can put behind a card at this solar elevation."""
    day = smoothstep(-0.18, 0.22, mu)
    zen = mix((0.012, 0.028, 0.085), (0.16, 0.44, 0.80), day)
    hor = mix((0.05, 0.075, 0.16),   (0.42, 0.66, 0.90), day)
    out = [tuple(min(255, c*255) for c in mix(hor, zen, h**0.85)) for h in (0.0, 0.5, 1.0)]
    out.append(tuple(min(255, 255*(0.99*day + 0.05)) for _ in range(3)))  # sunlit cloud
    return out

# ---------- the gate --------------------------------------------------------
BODY, LARGE = 4.5, 3.0
failures = []

def check(label, fg, need, card, mu):
    worst = min(ratio(hx(fg), over(card, sky, glass_alpha(mu))) for sky in skies(mu))
    if worst < need - 0.005:
        failures.append(f'mu={mu:+.2f} {label} {fg} -> {worst:.2f}:1 (need {need})')
    return worst

print('checking every solar elevation from -0.40 to 1.00 ...')
for i in range(-40, 101):
    mu = i / 100
    night = mu < 0.08
    pal   = NIGHT if night else LIGHT
    card  = DARK_GLASS if night else LIGHT_GLASS
    inks  = BAND_BRIGHT if night else BAND_INK

    check('ink',   pal['ink'],   BODY,  card, mu)
    check('dim',   pal['dim'],   BODY,  card, mu)
    check('muted', pal['muted'], BODY,  card, mu)
    check('good',  pal['good'],  LARGE, card, mu)
    check('burn',  pal['burn'],  LARGE, card, mu)
    for j, c in enumerate(inks):
        check(f'band[{j}]', c, LARGE, card, mu)

print(f'\n  light palette: {LIGHT}')
print(f'  night palette: {NIGHT}')
print(f'  band inks    : {BAND_INK}')
print(f'  glass alpha  : noon {glass_alpha(0.95):.2f} · twilight {glass_alpha(0.08):.2f} · night {glass_alpha(-0.3):.2f}')

if failures:
    print(f'\nFAIL — {len(failures)} contrast violations:')
    for f in failures[:12]:
        print('   ' + f)
    if len(failures) > 12:
        print(f'   ... and {len(failures)-12} more')
    sys.exit(1)
print('\n  PASS  every token clears WCAG AA at every solar elevation')
