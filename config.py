# =============================================================================
# config.py  --  Single source of truth for the banner generator.
# Fill this in (or let Claude fill it from your details), then run:
#     python generate_banner.py
# Outputs: output/dark.svg  and  output/light.svg
# =============================================================================

# ---- Identity ---------------------------------------------------------------
NAME          = "Aymane Fakihi"
USERNAME      = "AYMANEFAKIHI"        # profile repo is AYMANEFAKIHI/AYMANEFAKIHI, branch main
ROLE          = "Full-Stack Developer & Designer"
LOCATION      = "Rabat, Morocco"
EDUCATION     = "Software Eng. @ EMSI (2027)"
STATUS        = "Open to internships & freelance"
TOOLCHAIN     = "VS Code, Git, Docker, Figma"

# ---- Core stack -------------------------------------------------------------
LANGUAGES     = "JavaScript, TypeScript, Python"
FRONTEND      = "React, Next.js, TailwindCSS"
BACKEND       = "Node.js, REST, GraphQL"
DATABASE      = "MongoDB, PostgreSQL, MySQL"
INFRA         = "Docker, AWS, Vercel, Firebase"

# ---- Grid rows (label -> value). Order matters; leaders auto-computed. -------
MAIL          = "faymane12@gmail.com"
PORTFOLIO     = "portfolio (Vercel)"
LINKEDIN      = "aymane-fakihi"
FACEBOOK      = "—"

# ---- Photo ------------------------------------------------------------------
PHOTO_PATH    = "assets/photo.png"   # head-and-shoulders, flat bg, 1000px+ short edge

# ---- Three logos to morph between (SVG paths or PNG references) --------------
# Order = morph order after the portrait phase.
LOGOS = [
    "assets/logos/logo1.png",
    "assets/logos/logo2.png",
    "assets/logos/logo3.png",
]

# ---- Palette ----------------------------------------------------------------
# Rule: portrait hue MUST differ from UI chrome hue, or the face blends into
# its own frame.
PORTRAIT_DARK   = "#A78BFA"   # portrait dots in dark mode
PORTRAIT_LIGHT  = "#7C3AED"   # portrait dots in light mode
CHROME_DARK     = "#22D3EE"   # UI chrome (borders, labels) dark mode
CHROME_LIGHT    = "#0891B2"   # UI chrome light mode
ACCENT          = "#10B981"   # accent (LIVE badge glow, pill)
BG_DARK         = "#0A101F"   # panel background dark mode
BG_LIGHT        = "#F5F7FA"   # panel background light mode

# ---- Canvas -----------------------------------------------------------------
W, H          = 1180, 610
PORTRAIT_FRAC = 0.38          # left share of width for the VISUAL.MAP frame

# ---- Portrait pipeline knobs (tuned defaults; iterate on these) --------------
GRID_W, GRID_H = 300, 340
CONTRAST       = 1.30
UNSHARP_RADIUS = 3
UNSHARP_PCT    = 140
AUTOCONTRAST_CUTOFF = 1

# ---- Animation timing -------------------------------------------------------
INTRO_DUR      = 3.2          # seconds, plays once
LOOP_DUR       = 14.2         # seconds
PORTRAIT_HOLD  = 3.0
LOGO_HOLD      = 2.0
TRANSITION     = 1.3
N_INTRO_GROUPS = 60
N_DRIFT_BANDS  = 94
N_TRAVELLERS   = 900
DRIFT_FRAC     = 0.42         # how far a band drifts toward logo-1 centroid
DRIFT_NOISE_SIGMA = 4.0       # per-dot noise BEFORE grouping (defeats the grid trap)

# ---- Auto-calibration: target portrait dot count (None = manual contrast) --
TARGET_DOTS = 17000
