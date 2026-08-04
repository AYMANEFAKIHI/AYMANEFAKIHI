# =============================================================================
# pipeline.py  --  Portrait -> 1-bit dither -> dot coordinates.
# The .npy data this produces is the source of truth, not the SVG.
# =============================================================================
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from scipy import ndimage


def _prep_gray(img: Image.Image, grid_w, grid_h, contrast, cutoff,
               unsharp_radius, unsharp_pct) -> np.ndarray:
    """Crop-to-aspect, resize to grid, autocontrast, contrast, unsharp -> float [0,1]."""
    img = img.convert("RGB")
    # center-crop to the grid aspect (head+shoulders assumed already framed)
    target = grid_w / grid_h
    w, h = img.size
    if w / h > target:
        nw = int(h * target)
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target)
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    img = img.resize((grid_w, grid_h), Image.LANCZOS)
    g = img.convert("L")
    g = ImageOps.autocontrast(g, cutoff=cutoff)
    g = ImageEnhance.Contrast(g).enhance(contrast)
    g = g.filter(ImageFilter.UnsharpMask(radius=unsharp_radius, percent=unsharp_pct))
    return np.asarray(g, dtype=np.float64) / 255.0


def floyd_steinberg_serpentine(gray: np.ndarray) -> np.ndarray:
    """1-bit Floyd-Steinberg dither, serpentine scan. Returns bool (True=ink dot)."""
    a = gray.copy()
    h, w = a.shape
    out = np.zeros((h, w), dtype=bool)
    for y in range(h):
        rng = range(w) if y % 2 == 0 else range(w - 1, -1, -1)
        fwd = (y % 2 == 0)
        for x in rng:
            old = a[y, x]
            new = 1.0 if old >= 0.5 else 0.0
            out[y, x] = (new == 0.0)          # ink where the quantised pixel is dark
            err = old - new
            xr, xl = (x + 1, x - 1) if fwd else (x - 1, x + 1)
            if 0 <= xr < w:
                a[y, xr] += err * 7 / 16
            if y + 1 < h:
                if 0 <= xl < w:
                    a[y + 1, xl] += err * 3 / 16
                a[y + 1, x] += err * 5 / 16
                if 0 <= xr < w:
                    a[y + 1, xr] += err * 1 / 16
    return out


def _crop_to_aspect(img, grid_w, grid_h):
    target = grid_w / grid_h
    w, h = img.size
    if w / h > target:
        nw = int(h * target); return img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    nh = int(w / target); return img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))


def _keep_largest(mask):
    mask = ndimage.binary_fill_holes(mask)
    lbl, n = ndimage.label(mask)
    if n > 1:
        sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
        mask = (lbl == (np.argmax(sizes) + 1))
    return mask


def segment_subject(img: Image.Image, grid_w, grid_h,
                    rect_margin=(0.10, 0.05)) -> np.ndarray:
    """Return bool mask (True=subject). Prefers GrabCut (robust to gradient/
    vignetted studio backdrops); falls back to colour-distance thresholding.
    Head-and-shoulders subjects are centred, so a margin rect seeds the model."""
    img = _crop_to_aspect(img.convert("RGB"), grid_w, grid_h)
    try:
        import cv2
        work = img.resize((grid_w * 2, grid_h * 2), Image.LANCZOS)
        bgr = np.asarray(work)[:, :, ::-1].copy()
        H, W = bgr.shape[:2]
        m = np.zeros((H, W), np.uint8)
        mx, my = int(W * rect_margin[0]), int(H * rect_margin[1])
        rect = (mx, my, W - 2 * mx, H - my)          # subject reaches bottom edge
        bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        cv2.grabCut(bgr, m, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
        fg = np.isin(m, [cv2.GC_FGD, cv2.GC_PR_FGD])
        fg = ndimage.binary_opening(fg, iterations=2)   # sever thin bg bridges
        fg = _keep_largest(fg)
        small = np.asarray(Image.fromarray((fg * 255).astype(np.uint8)).resize(
            (grid_w, grid_h), Image.NEAREST)) > 127
        # drop tiny stray islands (specks) below 0.1% of the grid
        lbl, n = ndimage.label(small)
        if n > 1:
            sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
            keep = {i + 1 for i, s in enumerate(sizes) if s >= 0.001 * grid_w * grid_h}
            small = np.isin(lbl, list(keep))
        return small
    except Exception:
        arr = np.asarray(img.resize((grid_w, grid_h), Image.LANCZOS), dtype=np.float64)
        border = np.concatenate([arr[:6].reshape(-1, 3), arr[-6:].reshape(-1, 3),
                                 arr[:, :6].reshape(-1, 3), arr[:, -6:].reshape(-1, 3)])
        bg = np.median(border, axis=0)
        dist = np.sqrt(((arr - bg) ** 2).sum(axis=2))
        mask = dist > max(28.0, np.percentile(dist, 55))
        mask = ndimage.binary_closing(mask, structure=np.ones((3, 3)), iterations=2)
        return _keep_largest(mask)


def _apply_gamma(gray: np.ndarray, gamma: float) -> np.ndarray:
    return np.clip(gray, 0, 1) ** gamma


def calibrate_gamma(gray, mask, target_frac, dark, lo=0.35, hi=2.8, iters=16):
    """Binary-search a gamma so the dithered ink coverage (within mask if given)
    hits target_frac. Makes contrast self-tuning -> near-zero manual iteration.
    Returns (gamma, achieved_frac)."""
    def cover(gamma):
        g = _apply_gamma(gray, gamma)
        ink = floyd_steinberg_serpentine((1.0 - g) if dark else g)
        if mask is not None:
            m = ndimage.binary_erosion(mask, iterations=1)
            ink = ink & m
            denom = max(1, m.sum())
        else:
            denom = ink.size
        return ink.sum() / denom
    best = 1.0
    for _ in range(iters):
        mid = (lo + hi) / 2
        c = cover(mid)
        # higher gamma darkens -> fewer light-subject dots in dark mode; monotonic
        if (c > target_frac) == dark:
            lo = mid
        else:
            hi = mid
        best = mid
    return best, cover(best)


def portrait_dots(img: Image.Image, cfg, dark: bool):
    """Returns (xs, ys) int arrays of ink-dot grid coordinates for the given mode.
    dark: light dots draw the LIT subject, background segmented out.
    light: dark dots draw the DARK parts, background kept."""
    gray = _prep_gray(img, cfg.GRID_W, cfg.GRID_H, cfg.CONTRAST,
                      cfg.AUTOCONTRAST_CUTOFF, cfg.UNSHARP_RADIUS, cfg.UNSHARP_PCT)
    mask = segment_subject(img, cfg.GRID_W, cfg.GRID_H) if dark else None

    # optional auto-calibration: pick gamma to hit a target dot density, so the
    # portrait lands near the ideal ~17k dots without manual contrast fiddling.
    target = getattr(cfg, "TARGET_DOTS", None)
    if target:
        denom = mask.sum() if dark else gray.size
        gamma, _ = calibrate_gamma(gray, mask, target / max(1, denom), dark)
        gray = _apply_gamma(gray, gamma)

    if dark:
        # invert so bright subject pixels become ink dots on the dark panel
        ink = floyd_steinberg_serpentine(1.0 - gray)
        # hard-clear error-diffusion bleed just outside the mask edge
        eroded = ndimage.binary_erosion(mask, iterations=1)
        ink = ink & eroded
    else:
        ink = floyd_steinberg_serpentine(gray)
    ys, xs = np.where(ink)
    return xs.astype(np.int32), ys.astype(np.int32)


# ---- validation metrics -----------------------------------------------------
def evenness_metric(xs, ys, group_ids, grid_w, grid_h, n_groups):
    """~0.05 good (scattered), ~0.7 patchy. Each intro group should mirror the
    GLOBAL dot distribution (so dots appear everywhere at once). Reference is the
    actual dot spread, not the full grid -- in dark mode the segmented subject
    only occupies part of the frame."""
    ref = np.array([xs.std(), ys.std()])                 # global dot spread
    ref_mean = ref.mean() + 1e-9
    devs = []
    for g in range(n_groups):
        m = group_ids == g
        if m.sum() < 4:
            continue
        std = np.array([xs[m].std(), ys[m].std()])
        devs.append(np.abs(std - ref).mean() / ref_mean)
    return float(np.mean(devs)) if devs else 1.0
