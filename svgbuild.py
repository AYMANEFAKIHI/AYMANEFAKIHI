# =============================================================================
# svgbuild.py  --  Assemble dark.svg / light.svg from dots + motion data.
# Dots are emitted as <path> runs with shape-rendering="crispEdges".
# Two independent portrait layers (intro shimmer + loop drift) + travellers.
# =============================================================================
import numpy as np
from xml.sax.saxutils import escape


# ---- geometry ---------------------------------------------------------------
def portrait_box(cfg):
    """Inner box (x,y,w,h) for the portrait, inside the VISUAL.MAP frame."""
    bar = 34
    pad = 22
    fw = cfg.W * cfg.PORTRAIT_FRAC
    fx, fy = pad, bar + pad
    fh = cfg.H - fy - pad
    # fit GRID aspect inside the frame, centred
    ar = cfg.GRID_W / cfg.GRID_H
    inner_w, inner_h = fw - 2 * 14, fh - 2 * 14 - 20  # room for label
    if inner_w / inner_h > ar:
        h = inner_h; w = h * ar
    else:
        w = inner_w; h = w / ar
    bx = fx + 14 + (inner_w - w) / 2
    by = fy + 14 + 20 + (inner_h - h) / 2
    return bx, by, w, h


def _runs_path(xs, ys, ox, oy, cell):
    """Merge horizontal runs of dots per row into rect subpaths -> single 'd'."""
    if len(xs) == 0:
        return ""
    order = np.lexsort((xs, ys))
    xs, ys = xs[order], ys[order]
    d = []
    i, n = 0, len(xs)
    while i < n:
        y = ys[i]; x0 = xs[i]; x1 = xs[i]
        j = i + 1
        while j < n and ys[j] == y and xs[j] == x1 + 1:
            x1 = xs[j]; j += 1
        px = ox + x0 * cell
        py = oy + y * cell
        w = (x1 - x0 + 1) * cell
        d.append(f"M{px:.1f} {py:.1f}h{w:.1f}v{cell:.1f}h{-w:.1f}z")
        i = j
    return "".join(d)


# ---- info panel -------------------------------------------------------------
def _leaders(label, value, total_chars):
    """Dotted leader count from label/value length (never hand-edited)."""
    dots = max(3, total_chars - len(label) - len(value))
    return "." * dots


def info_panel_svg(cfg, chrome, fg):
    bar, pad = 34, 22
    x0 = cfg.W * cfg.PORTRAIT_FRAC + 16
    y = bar + pad + 24
    step = 23
    TOTAL = 74
    rows = [
        ("Subject", cfg.NAME), ("Role", cfg.ROLE), ("Origin", cfg.LOCATION),
        ("Education", cfg.EDUCATION), ("Status", cfg.STATUS), ("ToolChain", cfg.TOOLCHAIN),
        ("", ""),
        ("Core.Lang", cfg.LANGUAGES), ("Core.Frontend", cfg.FRONTEND),
        ("Core.Backend", cfg.BACKEND), ("Core.Database", cfg.DATABASE), ("Core.Infra", cfg.INFRA),
        ("", ""),
        ("Grid.Mail", cfg.MAIL), ("Grid.Portfolio", cfg.PORTFOLIO),
        ("Grid.LinkedIn", cfg.LINKEDIN), ("Grid.GitHub", cfg.USERNAME), ("Grid.Facebook", cfg.FACEBOOK),
    ]
    out = [f'<text x="{x0}" y="{bar+pad}" font-family="monospace" font-size="13" '
           f'fill="{chrome}" letter-spacing="2">SYSTEM.INFO</text>']
    for label, value in rows:
        if not label:
            y += step // 2
            continue
        lead = _leaders(label, value, TOTAL)
        vx = cfg.W - pad
        out.append(
            f'<text x="{x0}" y="{y}" font-family="monospace" font-size="14" fill="{chrome}">'
            f'{escape(label)} <tspan fill="{fg}" opacity="0.45">{lead}</tspan></text>'
            f'<text x="{vx}" y="{y}" font-family="monospace" font-size="14" fill="{fg}" '
            f'text-anchor="end" textLength="{max(1,len(value))*8.4:.0f}" '
            f'lengthAdjust="spacingAndGlyphs">{escape(value)}</text>')
        y += step
    return "\n".join(out)


# ---- animation: portrait layers + travellers --------------------------------
def portrait_layers(cfg, xs, ys, intro_g, bands, centroid, box):
    bx, by, w, h = box
    cell = w / cfg.GRID_W
    fg_intro = []
    # ---- Layer 1: intro shimmer (grouped by scattered intro groups) ----
    for g in range(cfg.N_INTRO_GROUPS):
        m = intro_g == g
        if not m.any():
            continue
        d = _runs_path(xs[m], ys[m], bx, by, cell)
        begin = (g / cfg.N_INTRO_GROUPS) * 2.0
        fg_intro.append(
            f'<path d="{d}" opacity="0">'
            f'<animate attributeName="opacity" begin="{begin:.2f}s" dur="0.9s" '
            f'values="0;1" fill="freeze"/></path>')
    intro_layer = (f'<g shape-rendering="crispEdges" fill="__PORTRAIT__">'
                   f'<animate attributeName="opacity" begin="{cfg.INTRO_DUR:.2f}s" '
                   f'dur="0.4s" values="1;0" fill="freeze"/>'
                   + "".join(fg_intro) + '</g>')

    # ---- Layer 2: loop drift bands (translate toward centroid + fade) ----
    cx = bx + centroid[0] * cell
    cy = by + centroid[1] * cell
    loop_bands = []
    for b in range(cfg.N_DRIFT_BANDS):
        m = bands == b
        if not m.any():
            continue
        mx = bx + xs[m].mean() * cell
        my = by + ys[m].mean() * cell
        dx = (cx - mx) * cfg.DRIFT_FRAC
        dy = (cy - my) * cfg.DRIFT_FRAC
        d = _runs_path(xs[m], ys[m], bx, by, cell)
        # uneven keyTimes: hold portrait, drift out during logo phase, return
        loop_bands.append(
            f'<path d="{d}">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'begin="{cfg.INTRO_DUR:.2f}s" dur="{cfg.LOOP_DUR:.2f}s" repeatCount="indefinite" '
            f'keyTimes="0;0.21;0.30;0.80;0.91;1" '
            f'values="0 0;0 0;{dx:.1f} {dy:.1f};{dx:.1f} {dy:.1f};0 0;0 0"/>'
            f'<animate attributeName="opacity" begin="{cfg.INTRO_DUR:.2f}s" '
            f'dur="{cfg.LOOP_DUR:.2f}s" repeatCount="indefinite" '
            f'keyTimes="0;0.21;0.34;0.78;0.91;1" values="1;1;0.15;0.15;1;1"/></path>')
    loop_layer = (f'<g shape-rendering="crispEdges" fill="__PORTRAIT__" opacity="0">'
                  f'<animate attributeName="opacity" begin="{cfg.INTRO_DUR:.2f}s" '
                  f'dur="0.4s" values="0;1" fill="freeze"/>'
                  + "".join(loop_bands) + '</g>')
    return intro_layer + loop_layer


def travellers_layer(cfg, aligned, box):
    """900 dots morphing between logos via OT, hidden during the portrait phase."""
    bx, by, w, h = box
    tb = min(w, h) * 0.42
    cx, cy = bx + w / 2, by + h / 2
    def place(pts):
        return np.stack([cx + pts[:, 0] * tb, cy + pts[:, 1] * tb], axis=1)
    frames = [place(p) for p in aligned]           # A,B,C,A  (loop closed)
    n = len(frames[0])
    # keyTimes across LOOP_DUR: portrait(hold) 0-0.21, then logos with transitions
    kt = "0;0.21;0.30;0.44;0.53;0.67;0.76;0.90;1"
    # opacity: hidden during portrait, visible during logo phases
    op = "0;0;1;1;1;1;1;0;0"
    dots = []
    size = max(1.4, (w / cfg.GRID_W) * 1.7)
    for i in range(n):
        # x/y value strings across the 4 logo frames (A,B,C,A) + holds
        pxs = [frames[k][i, 0] for k in range(4)]
        pys = [frames[k][i, 1] for k in range(4)]
        # match kt slots: hold@A, A, ->B, B, ->C, C, ->A, A, hold
        vx = f"{pxs[0]:.1f};{pxs[0]:.1f};{pxs[0]:.1f};{pxs[1]:.1f};{pxs[1]:.1f};{pxs[2]:.1f};{pxs[2]:.1f};{pxs[3]:.1f};{pxs[3]:.1f}"
        vy = f"{pys[0]:.1f};{pys[0]:.1f};{pys[0]:.1f};{pys[1]:.1f};{pys[1]:.1f};{pys[2]:.1f};{pys[2]:.1f};{pys[3]:.1f};{pys[3]:.1f}"
        dots.append(
            f'<rect width="{size:.1f}" height="{size:.1f}" x="{pxs[0]:.1f}" y="{pys[0]:.1f}" opacity="0">'
            f'<animate attributeName="x" begin="{cfg.INTRO_DUR:.2f}s" dur="{cfg.LOOP_DUR:.2f}s" '
            f'repeatCount="indefinite" keyTimes="{kt}" values="{vx}"/>'
            f'<animate attributeName="y" begin="{cfg.INTRO_DUR:.2f}s" dur="{cfg.LOOP_DUR:.2f}s" '
            f'repeatCount="indefinite" keyTimes="{kt}" values="{vy}"/>'
            f'<animate attributeName="opacity" begin="{cfg.INTRO_DUR:.2f}s" dur="{cfg.LOOP_DUR:.2f}s" '
            f'repeatCount="indefinite" keyTimes="{kt}" values="{op}"/></rect>')
    return (f'<g shape-rendering="crispEdges" fill="__ACCENT__">' + "".join(dots) + '</g>')


# ---- chrome + document ------------------------------------------------------
def build_document(cfg, dark, xs, ys, intro_g, bands, centroid, aligned):
    portrait = cfg.PORTRAIT_DARK if dark else cfg.PORTRAIT_LIGHT
    chrome = cfg.CHROME_DARK if dark else cfg.CHROME_LIGHT
    bg = cfg.BG_DARK if dark else cfg.BG_LIGHT
    fg = "#E6EDF7" if dark else "#1B2430"
    box = portrait_box(cfg)
    bx, by, w, h = box
    bar, pad = 34, 22
    fw = cfg.W * cfg.PORTRAIT_FRAC

    layers = portrait_layers(cfg, xs, ys, intro_g, bands, centroid, box)
    trav = travellers_layer(cfg, aligned, box)
    portrait_group = (layers + trav).replace("__PORTRAIT__", portrait).replace("__ACCENT__", cfg.ACCENT)
    info = info_panel_svg(cfg, chrome, fg)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cfg.W} {cfg.H}"
  width="{cfg.W}" height="{cfg.H}" font-family="monospace">
<rect width="{cfg.W}" height="{cfg.H}" rx="10" fill="{bg}"/>
<rect width="{cfg.W}" height="{bar}" rx="10" fill="{bg}" stroke="{chrome}" stroke-opacity="0.35"/>
<circle cx="20" cy="17" r="5" fill="#ff5f57"/><circle cx="38" cy="17" r="5" fill="#febc2e"/>
<circle cx="56" cy="17" r="5" fill="#28c840"/>
<text x="{cfg.W/2}" y="22" text-anchor="middle" font-size="13" fill="{chrome}"
  opacity="0.8">profile.sh --live</text>
<rect x="{cfg.W-96}" y="9" width="72" height="18" rx="9" fill="none"
  stroke="#ff5f57" stroke-opacity="0.5"/>
<circle cx="{cfg.W-84}" cy="18" r="4" fill="#ff3b30">
  <animate attributeName="opacity" dur="1.4s" repeatCount="indefinite" values="1;0.2;1"/></circle>
<text x="{cfg.W-72}" y="22" font-size="12" fill="#ff5f57">LIVE</text>
<rect x="{pad}" y="{bar+pad}" width="{fw-2*14}" height="{cfg.H-bar-2*pad}" rx="6"
  fill="none" stroke="{chrome}" stroke-opacity="0.35"/>
<text x="{pad+8}" y="{bar+pad+16}" font-size="12" fill="{chrome}" letter-spacing="2">VISUAL.MAP</text>
<clipPath id="pc"><rect x="{bx-2}" y="{by-2}" width="{w+4}" height="{h+4}" rx="4"/></clipPath>
<g clip-path="url(#pc)">{portrait_group}</g>
{info}
<rect x="{cfg.W*cfg.PORTRAIT_FRAC+16}" y="{cfg.H-pad-4}" width="{len(cfg.USERNAME)*9+34}" height="22"
  rx="11" fill="{cfg.ACCENT}" fill-opacity="0.18" stroke="{cfg.ACCENT}" stroke-opacity="0.6"/>
<text x="{cfg.W*cfg.PORTRAIT_FRAC+28}" y="{cfg.H-pad+11}" font-size="14" fill="{cfg.ACCENT}">@{escape(cfg.USERNAME)}</text>
</svg>'''
    return svg
