# amicookedtoday.com

Today's UV, the minutes you need for vitamin D, and the minutes before you burn —
for your skin, in your city.

One static HTML file. No build step, no framework, no dependencies at runtime.
`npm` is only used for the CI checks.

## Run it

Open `index.html`. That's it.

Only caveat: "use my location" needs HTTPS (`navigator.geolocation` requires a
secure context), so over `file://` it falls back to IP lookup.

## Deploy

Netlify auto-deploys `main`. `netlify.toml` sets the headers — including
`Permissions-Policy: geolocation=(self)`, without which the pin button is blocked.

## The science

Vitamin D times come from Kift & Webb (2024), *Nutrients* 16:1489
(https://doi.org/10.3390/nu16101489) — the maintenance-dose method. Burn times
come from Fitzpatrick MED values and the live UV index.

Live UV is Open-Meteo's `uv_index` (GFS-derived, includes cloud cover).
**Their free tier is non-commercial only** and the data is CC-BY 4.0 — the
attribution in the About panel is a licence condition, not decoration.

## Things that look arbitrary but are not

Read this before changing them.

**Glass opacity (`applySkyTheme`).** Noon 0.48, twilight 0.63, night 0.34. These
are the verified minimums for WCAG AA at each solar elevation. The card sits on a
live shader, so its backdrop ranges from a night sky to a sunlit cloud; a single
opacity can't hold contrast across both, which is why the theme AND the alpha
follow the sun. `scripts/check_contrast.py` re-derives this on every push.

**Backdrop blur is 12px, not 30.** A heavier blur averages the drifting leaves out
of existence. Contrast was solved against worst-case *point* colours, never the
blurred average, so low blur is safe.

**Two palettes.** Each UV band has `col` (bright — sky tint, gauge arc on dark
glass) and `ink` (dark — text on light glass). The teal that glows on the sky is
unreadable on white.

**`SPF_LIST` is an array, not an object.** JS reorders integer-like keys ahead of
string keys, which silently pushed "None" to the end of the row.

**`min-inline-size: 0` on fieldsets.** `<fieldset>` has an implicit
`min-inline-size: min-content` that overrides `1fr` and overflows grid tracks.
The `legend { float: left }` next to it is the companion fix — a `<legend>`
renders into the border box, where `margin-bottom` is ignored.

**The UV model's ozone term.** `12.5 * cos(SZA)^2.42` alone runs ~3 points hot at
mid-latitudes. The van Heuklon (1979) ozone climatology plus a turbidity factor
brings mean error against NOAA/EPA city forecasts from 3.0 to ~1.2. The 290 DU
floor is a guard rail on the `-1.23` exponent over-amplifying in the tropics —
not a claim about tropical ozone.

**Timezones use `Intl`, not `round(lon/15)`.** The naive version ignores DST and
can't express Kathmandu (+5:45) or Kolkata (+5:30).

**The 450ms grace timer in `loadPlace`.** Modeled values are computed instantly
but held back, so fast connections go straight to live and never see the dial
jump. Slow or offline ones still get a working page.

## Checks

    npm install --prefix scripts
    node   scripts/check_js.mjs         # syntax + script-tag integrity
    node   scripts/check_shader.mjs     # GLSL parses, ES 1.0 rules
    python3 scripts/check_fixes.py      # 34-point regression checklist
    python3 scripts/check_contrast.py   # WCAG AA at every solar elevation

CI runs all four on every push. Netlify won't publish a red commit.
