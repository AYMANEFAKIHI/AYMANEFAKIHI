# =============================================================================
# preflight.py  --  Score a candidate photo BEFORE running the pipeline.
#   python preflight.py assets/photo.jpg
# Reports resolution, background flatness, subject/background separation, and
# lighting evenness, then a verdict on whether it will dither well.
# =============================================================================
import sys
import numpy as np
from PIL import Image
from scipy import ndimage


def score(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    arr = np.asarray(img, np.float64)
    short_edge = min(w, h)

    # background = border frame; flatness = how uniform its colour is
    b = np.concatenate([
        arr[:8].reshape(-1, 3), arr[-8:].reshape(-1, 3),
        arr[:, :8].reshape(-1, 3), arr[:, -8:].reshape(-1, 3)])
    bg = np.median(b, 0)
    bg_std = float(np.sqrt(((b - bg) ** 2).sum(1)).std())     # low = flat wall

    # subject separation = colour distance of centre region from bg
    small = np.asarray(img.resize((300, 340), Image.LANCZOS), np.float64)
    dist = np.sqrt(((small - bg) ** 2).sum(2))
    sep = float(np.percentile(dist, 60))                       # high = separated
    mask = dist > max(28, np.percentile(dist, 55))
    mask = ndimage.binary_fill_holes(mask)
    subj_frac = float(mask.mean())                             # subject coverage

    # lighting evenness on the face/subject = local contrast variance (harsh
    # shadows survive dithering as blotches)
    g = np.asarray(img.convert("L").resize((300, 340), Image.LANCZOS), np.float64)
    if mask.any():
        sv = g[mask]
        shadow_spread = float(np.percentile(sv, 90) - np.percentile(sv, 10))
    else:
        shadow_spread = 999

    print(f"photo: {path}  ({w}x{h})")
    print(f"  short edge      : {short_edge:>5}px      {'OK' if short_edge>=1000 else 'LOW  (<1000)'}")
    print(f"  background flat  : {bg_std:6.1f}        {'OK' if bg_std<22 else 'BUSY (want <22)'}")
    print(f"  subj separation  : {sep:6.1f}        {'OK' if sep>45 else 'WEAK (want >45)'}")
    print(f"  subject coverage : {subj_frac*100:5.1f}%       {'OK' if 0.18<subj_frac<0.75 else 'reframe head+shoulders'}")
    print(f"  lighting spread  : {shadow_spread:6.1f}        {'OK' if shadow_spread<170 else 'HARSH (may blotch)'}")

    good = (short_edge >= 1000 and bg_std < 22 and sep > 45 and 0.18 < subj_frac < 0.75)
    print("  VERDICT:", "will dither well" if good else
          "workable, but expect extra contrast/crop iteration on the flagged items")
    return good


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "assets/photo.jpg"
    score(p)
