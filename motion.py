# =============================================================================
# motion.py  --  Grouping + morph maths for the two-layer animation.
#   Layer 1 (portrait): intro scatter groups + loop drift bands.
#   Layer 2 (travellers): optimal-transport morph between logos.
# =============================================================================
import numpy as np
from scipy.optimize import linear_sum_assignment
from PIL import Image


# ---- Layer 1: intro scatter groups ------------------------------------------
def intro_groups(n_dots, n_groups, seed=7):
    """Fully random group ids -> every group is scattered across the whole
    portrait, so dots appear everywhere at once and thicken together."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, n_groups, size=n_dots)


# ---- Layer 1: loop drift bands (the grid trap lives here) -------------------
def _smooth_noise_field(xs, ys, cell=26, seed=21):
    """Low-frequency value noise sampled at each dot: a coarse random lattice,
    bilinearly interpolated. Makes band boundaries wobble organically instead of
    following a near-linear scalar (which recreates the grid/stripe trap)."""
    rng = np.random.default_rng(seed)
    gx = int((xs.max() - xs.min()) / cell) + 3
    gy = int((ys.max() - ys.min()) / cell) + 3
    lat = rng.standard_normal((gy, gx))
    fx = (xs - xs.min()) / cell
    fy = (ys - ys.min()) / cell
    ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - ix, fy - iy
    v00 = lat[iy, ix];     v10 = lat[iy, ix + 1]
    v01 = lat[iy + 1, ix]; v11 = lat[iy + 1, ix + 1]
    return (v00 * (1 - tx) * (1 - ty) + v10 * tx * (1 - ty)
            + v01 * (1 - tx) * ty + v11 * tx * ty)


def drift_bands(xs, ys, centroid, n_bands, noise_sigma, seed=11):
    """Band dots by their drift scalar (distance toward the logo centroid), but
    add BOTH per-dot noise and a smooth low-frequency spatial noise field before
    quantizing -- otherwise the near-linear drift scalar recreates a grid/stripe
    and the dissolve looks blocky."""
    rng = np.random.default_rng(seed)
    pts = np.stack([xs, ys], axis=1).astype(np.float64)
    pts_noisy = pts + rng.normal(0, noise_sigma, pts.shape)
    d = centroid - pts_noisy
    scalar = np.hypot(d[:, 0], d[:, 1])                 # distance to centroid
    rng_span = scalar.max() - scalar.min() + 1e-9
    field = _smooth_noise_field(xs, ys)                 # ~unit std
    scalar = scalar + 0.55 * rng_span * field           # wobble the band order
    order = np.argsort(scalar)
    bands = np.empty(len(xs), dtype=np.int32)
    edges = np.array_split(order, n_bands)
    for b, idx in enumerate(edges):
        bands[idx] = b
    return bands


def band_linearity(xs, ys, bands):
    """Grid-trap proxy: R^2 of band id explained by a linear model of (x,y).
    ~1.0 = you built a grid (bad); lower = organic. Report honestly."""
    A = np.stack([xs, ys, np.ones_like(xs)], axis=1).astype(np.float64)
    coef, *_ = np.linalg.lstsq(A, bands.astype(np.float64), rcond=None)
    pred = A @ coef
    ss_res = ((bands - pred) ** 2).sum()
    ss_tot = ((bands - bands.mean()) ** 2).sum()
    return float(1 - ss_res / ss_tot)


# ---- Layer 2: logo point sampling -------------------------------------------
def sample_logo_points(path, n, seed=3):
    """Load a raster logo (PNG/JPG, dark ink on light) and sample n ink points,
    normalised to a unit box centred at origin."""
    img = Image.open(path).convert("L")
    a = np.asarray(img, dtype=np.float64) / 255.0
    ink = a < 0.5
    ys, xs = np.where(ink)
    if len(xs) == 0:
        raise ValueError(f"No ink found in {path}")
    rng = np.random.default_rng(seed)
    if len(xs) >= n:
        pick = rng.choice(len(xs), n, replace=False)
    else:
        pick = rng.choice(len(xs), n, replace=True)
    pts = np.stack([xs[pick], ys[pick]], axis=1).astype(np.float64)
    pts -= pts.mean(0)
    scale = np.abs(pts).max()
    return pts / (scale + 1e-9)


def ot_match(src, dst):
    """Optimal-transport assignment (min total squared distance) so each dot
    takes the shortest path. Returns dst reordered to align with src."""
    cost = ((src[:, None, :] - dst[None, :, :]) ** 2).sum(axis=2)
    r, c = linear_sum_assignment(cost)
    out = np.empty_like(dst)
    out[r] = dst[c]
    return out


def morph_chain(logo_pts):
    """Given [A,B,C] point sets (equal length), OT-align each to the next in a
    loop A->B->C->A so every traveller has a coherent shortest-path trajectory."""
    n = len(logo_pts)
    aligned = [logo_pts[0]]
    for i in range(1, n):
        aligned.append(ot_match(aligned[-1], logo_pts[i]))
    # close the loop back to A
    aligned.append(ot_match(aligned[-1], aligned[0]))
    return aligned
