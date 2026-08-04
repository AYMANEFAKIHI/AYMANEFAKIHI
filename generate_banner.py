# =============================================================================
# generate_banner.py  --  Orchestrates the full banner build.
#   python generate_banner.py
# Writes output/dark.svg, output/light.svg, and build/*.npy (source of truth).
# =============================================================================
import os
import numpy as np
from PIL import Image
import config as cfg
import pipeline as P
import motion as M
import svgbuild as S

os.makedirs("build", exist_ok=True)
os.makedirs("output", exist_ok=True)


def build_mode(dark: bool):
    tag = "dark" if dark else "light"
    img = Image.open(cfg.PHOTO_PATH)
    xs, ys = P.portrait_dots(img, cfg, dark=dark)
    np.save(f"build/{tag}_xs.npy", xs)
    np.save(f"build/{tag}_ys.npy", ys)

    centroid = np.array([xs.mean(), ys.mean()])
    intro_g = M.intro_groups(len(xs), cfg.N_INTRO_GROUPS)
    bands = M.drift_bands(xs, ys, centroid, cfg.N_DRIFT_BANDS, cfg.DRIFT_NOISE_SIGMA)

    # metrics
    even = P.evenness_metric(xs, ys, intro_g, cfg.GRID_W, cfg.GRID_H, cfg.N_INTRO_GROUPS)
    grid = M.band_linearity(xs, ys, bands)

    # travellers
    logo_pts = [M.sample_logo_points(p, cfg.N_TRAVELLERS, seed=10 + i)
                for i, p in enumerate(cfg.LOGOS)]
    aligned = M.morph_chain(logo_pts)

    svg = S.build_document(cfg, dark, xs, ys, intro_g, bands, centroid, aligned)
    path = f"output/{tag}.svg"
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    size_kb = os.path.getsize(path) / 1024
    print(f"[{tag}] dots={len(xs):>6}  evenness={even:.3f} (aim ~0.05)  "
          f"band_linearity={grid:.3f} (lower=organic)  size={size_kb:.0f}KB")
    return even, grid, size_kb


if __name__ == "__main__":
    for d in (True, False):
        build_mode(d)
    print("done -> output/dark.svg, output/light.svg")
