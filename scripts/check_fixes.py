#!/usr/bin/env python3
"""
Regression checklist.

Every entry here is a bug that was found, diagnosed and fixed once. They are
mostly invisible: the ozone term, the DST-aware timezones, the JS key-ordering
trap that put "None" last in the SPF row. Nothing throws if they regress — the
numbers just quietly go wrong. This is the net.
"""
import re, sys

src = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html').read()

CHECKS = [
 # --- location / timezone -------------------------------------------------
 ("bundled city list present",        lambda s: s.count('|America/') > 30),
 ("257 bundled cities",               lambda s: len(re.search(r'const CITY_RAW = `\n(.*?)\n`;', s, re.S).group(1).strip().split('\n')) == 257),
 ("every city has an IANA tz",        lambda s: all(len(l.split('|')) == 6 and l.split('|')[5]
                                        for l in re.search(r'const CITY_RAW = `\n(.*?)\n`;', s, re.S).group(1).strip().split('\n'))),
 ("DST-aware tzOffsetHours via Intl", lambda s: 'tzOffsetHours' in s and 'longOffset' in s),
 ("tz threaded into loadPlace",       lambda s: re.search(r'async function loadPlace\(lat, lon, label, tz\)', s)),
 ("browser tz for geolocation",       lambda s: 'resolvedOptions().timeZone' in s),
 ("3 IP providers w/ timeout",        lambda s: s.count("{u:'https://") >= 3 and 'AbortController' in s),

 # --- UV model ------------------------------------------------------------
 ("van Heuklon ozone climatology",    lambda s: 'ozoneDU' in s and '0.9865' in s),
 ("ozone term in UVI formula",        lambda s: '-1.23' in s),
 ("aerosol turbidity factor",         lambda s: 'AEROSOL' in s and '0.92' in s),
 ("ozone floor 290 guard rail",       lambda s: 'Math.max(du, 290)' in s),
 ("southern-hemisphere ozone branch", lambda s: 'n-152' in s.replace(' ', '') or '(n-152)' in s.replace(' ', '')),

 # --- live data -----------------------------------------------------------
 ("open-meteo forecast endpoint",     lambda s: 'api.open-meteo.com/v1/forecast' in s),
 ("clear-sky ceiling requested",      lambda s: 'uv_index_clear_sky' in s),
 ("cloud delta surfaced",             lambda s: 'uvCeil' in s),
 # regression: the note once compared today's clear-sky PEAK against the CURRENT
 # UV, so at dusk it blamed sunset on cloud ("taking 7.5 off" at UV 0.7).
 ("cloud delta compares like w/ like", lambda s: 'uvCeilNow' in s and 'uvCeilNow - now' in s
                                        and 'state.uvCeil - now' not in s),
 ("hourly clear-sky stored",          lambda s: 'clear:Math.max(cs[i]' in s),
 ("live vs modeled source tag",       lambda s: 'setSource' in s and 'live feed unreachable' in s),

 # --- gauge ---------------------------------------------------------------
 ("gauge shows current UV",           lambda s: 'const now = state.uv' in s and 'headline = the UV right now' in s),
 ("gauge auto-extends past 12",       lambda s: 'gaugeTop' in s and '16' in s and '20' in s),
 ("dose math still uses peak",        lambda s: 'dose math still uses' in s),

 # --- SPF -----------------------------------------------------------------
 ("SPF is an ordered array",          lambda s: 'SPF_LIST' in s),
 ("None is first",                    lambda s: re.search(r"SPF_LIST\s*=\s*\[\s*\n?\s*\{key:'None'", s)),
 ("SPF 40/70/100 options",            lambda s: all(f"key:'{k}'" in s.replace(' ', '') or f"key:'{k}'" in s for k in ['40','70','100'])),
 ("real-world SPF = sqrt",            lambda s: 'Math.sqrt(f)' in s),
 ("spfRange shows the spread",        lambda s: 'spfRange' in s),

 # --- vitamin D / burn ----------------------------------------------------
 ("vitamin D scales with SPF",        lambda s: re.search(r'vdMinsAt[\s\S]{0,220}effSPF\(\)', s)),
 ("vitamin D blocked > 240min",       lambda s: '240' in s),
 ("Vitamin D Winter below UVI 1",     lambda s: re.search(r'if\(uv < 1\) return null', s)),
 ("burn uses MED/(uv*1.5)",           lambda s: 'uv*1.5' in s),
 ("curve window 6am-8pm",             lambda s: 'h.hour>=6 && h.hour<=20' in s),
 ("y-axis ticks + gridlines",         lambda s: 'ytick' in s and 'gline' in s),
 ("whole-day framing callout",        lambda s: 'per-day' in s and 'not per-hour' in s.lower()),

 # --- honest copy ---------------------------------------------------------
 ("Fitzpatrick VI honest copy",       lambda s: 'not immunity' in s),
 ("GFS provenance (not CAMS)",        lambda s: 'GFS' in s),
 ("paper cited",                      lambda s: 'Kift' in s),
]

fails = []
for name, fn in CHECKS:
    try:
        ok = bool(fn(src))
    except Exception as e:
        ok = False
        name += f"  [{type(e).__name__}]"
    print(("  PASS  " if ok else "  FAIL  ") + name)
    if not ok:
        fails.append(name)

print()
print(f"{len(CHECKS)-len(fails)}/{len(CHECKS)} fixes intact")
if fails:
    print("REGRESSED:")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
