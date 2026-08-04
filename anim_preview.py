# Renders the loop timeline to an animated GIF using the SAME motion math the
# SVG emits, so the animation is verified as MOTION, not just structure.
import numpy as np
from PIL import Image, ImageDraw
import config as cfg
import motion as M
import svgbuild as S

def hexrgb(h): h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))

def interp(t, keytimes, values):
    """Piecewise-linear SMIL interpolation (values may be scalars or 2-vectors)."""
    kt = np.array(keytimes)
    i = np.searchsorted(kt, t, side="right") - 1
    i = np.clip(i, 0, len(kt) - 2)
    span = kt[i+1] - kt[i]
    f = 0.0 if span <= 0 else (t - kt[i]) / span
    return np.array(values[i]) + f * (np.array(values[i+1]) - np.array(values[i]))

def render_gif(frames=44, scale=0.78):
    tag = "dark"
    xs = np.load(f"build/{tag}_xs.npy"); ys = np.load(f"build/{tag}_ys.npy")
    centroid = np.array([xs.mean(), ys.mean()])
    bands = M.drift_bands(xs, ys, centroid, cfg.N_DRIFT_BANDS, cfg.DRIFT_NOISE_SIGMA)
    logo_pts = [M.sample_logo_points(p, cfg.N_TRAVELLERS, seed=10+i) for i,p in enumerate(cfg.LOGOS)]
    aligned = M.morph_chain(logo_pts)

    bx,by,w,h = S.portrait_box(cfg); cell = w/cfg.GRID_W
    bg = hexrgb(cfg.BG_DARK); portrait = hexrgb(cfg.PORTRAIT_DARK)
    chrome = hexrgb(cfg.CHROME_DARK); accent = hexrgb(cfg.ACCENT)
    cx = bx + centroid[0]*cell; cy = by + centroid[1]*cell

    # precompute per-band mean + target offset
    binfo = []
    for b in range(cfg.N_DRIFT_BANDS):
        m = bands==b
        if not m.any(): continue
        mx = bx+xs[m].mean()*cell; my = by+ys[m].mean()*cell
        dx = (cx-mx)*cfg.DRIFT_FRAC; dy=(cy-my)*cfg.DRIFT_FRAC
        binfo.append((xs[m], ys[m], dx, dy))

    # traveller frame positions (A,B,C,A) in pixels
    tb = min(w,h)*0.42; tcx,tcy = bx+w/2, by+h/2
    tframes = [np.stack([tcx+p[:,0]*tb, tcy+p[:,1]*tb],1) for p in aligned]
    kt_t = [0,0.21,0.30,0.44,0.53,0.67,0.76,0.90,1.0]
    op_t = [0,0,1,1,1,1,1,0,0]
    slot = [0,0,0,1,1,2,2,3,3]  # which of A,B,C,A frame each keytime uses
    tsize = max(1.4,(w/cfg.GRID_W)*1.7)

    kt_tr = [0,0.21,0.30,0.80,0.91,1.0]
    kt_op = [0,0.21,0.34,0.78,0.91,1.0]
    op_vals = [1,1,0.15,0.15,1,1]

    imgs=[]
    for fr in range(frames):
        t = fr/(frames-1)
        im = Image.new("RGB",(cfg.W,cfg.H),bg); d=ImageDraw.Draw(im)
        d.rectangle([0,0,cfg.W-1,34],outline=chrome)
        d.rectangle([22,56,cfg.W*cfg.PORTRAIT_FRAC-14,cfg.H-22],outline=chrome)
        # portrait drift bands
        off = interp(t, kt_tr, [(0,0),(0,0),(1,1),(1,1),(0,0),(0,0)])
        opa = float(interp(t, kt_op, [[v] for v in op_vals])[0])
        pcol = tuple(int(c*opa+b0*(1-opa)) for c,b0 in zip(portrait,bg))
        for (bxs,bys,dx,dy) in binfo:
            ox=off[0]*dx; oy=off[1]*dy
            for x,y in zip(bxs,bys):
                px=bx+x*cell+ox; py=by+y*cell+oy
                d.rectangle([px,py,px+cell,py+cell],fill=pcol)
        # travellers
        to = float(interp(t, kt_t, [[v] for v in op_t])[0])
        if to>0.02:
            # interpolate positions between slot frames
            kt=np.array(kt_t); i=np.clip(np.searchsorted(kt,t,'right')-1,0,len(kt)-2)
            span=kt[i+1]-kt[i]; f=0 if span<=0 else (t-kt[i])/span
            P0=tframes[slot[i]]; P1=tframes[slot[i+1]]; pos=P0+f*(P1-P0)
            tcol=tuple(int(c*to+b0*(1-to)) for c,b0 in zip(accent,bg))
            for px,py in pos:
                d.rectangle([px,py,px+tsize,py+tsize],fill=tcol)
        # LIVE dot
        d.ellipse([cfg.W-88,14,cfg.W-80,22],fill=(255,59,48) if (fr//4)%2 else (120,30,25))
        imgs.append(im.resize((int(cfg.W*scale),int(cfg.H*scale)),Image.LANCZOS).convert("P",palette=Image.ADAPTIVE,colors=64))
    imgs[0].save("build/loop_preview.gif",save_all=True,append_images=imgs[1:],
                 duration=int(cfg.LOOP_DUR*1000/frames),loop=0,optimize=False,disposal=2)
    print(f"build/loop_preview.gif  ({frames} frames, {cfg.LOOP_DUR}s loop)")

if __name__=="__main__":
    render_gif()
