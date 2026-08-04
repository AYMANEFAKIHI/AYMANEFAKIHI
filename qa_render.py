# QA-only static rasteriser: composes the banner's first-frame look to PNG so a
# human (or Claude) can eyeball dither/segmentation/layout. NOT the deliverable.
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import config as cfg
import svgbuild as S

def hexrgb(h): h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))

def render(dark):
    tag = "dark" if dark else "light"
    xs = np.load(f"build/{tag}_xs.npy"); ys = np.load(f"build/{tag}_ys.npy")
    bg = hexrgb(cfg.BG_DARK if dark else cfg.BG_LIGHT)
    portrait = hexrgb(cfg.PORTRAIT_DARK if dark else cfg.PORTRAIT_LIGHT)
    chrome = hexrgb(cfg.CHROME_DARK if dark else cfg.CHROME_LIGHT)
    im = Image.new("RGB", (cfg.W, cfg.H), bg); d = ImageDraw.Draw(im)
    bar, pad = 34, 22
    fw = cfg.W * cfg.PORTRAIT_FRAC
    # title bar + frames
    d.rectangle([0,0,cfg.W-1,bar], outline=chrome)
    for i,c in enumerate(["#ff5f57","#febc2e","#28c840"]):
        d.ellipse([15+i*18,12,25+i*18,22], fill=hexrgb(c))
    d.rectangle([pad,bar+pad,fw-14,cfg.H-pad], outline=chrome)
    # portrait dots
    bx,by,w,h = S.portrait_box(cfg); cell = w/cfg.GRID_W
    for x,y in zip(xs,ys):
        px,py = bx+x*cell, by+y*cell
        d.rectangle([px,py,px+cell,py+cell], fill=portrait)
    # info rows (approx)
    fg = hexrgb("#E6EDF7" if dark else "#1B2430")
    try: font = ImageFont.truetype("consola.ttf", 14)
    except: font = ImageFont.load_default()
    x0 = cfg.W*cfg.PORTRAIT_FRAC+16; yy = bar+pad+22; step=23
    rows=[("Subject",cfg.NAME),("Role",cfg.ROLE),("Origin",cfg.LOCATION),
          ("Education",cfg.EDUCATION),("Status",cfg.STATUS),("ToolChain",cfg.TOOLCHAIN),("",""),
          ("Core.Lang",cfg.LANGUAGES),("Core.Frontend",cfg.FRONTEND),("Core.Backend",cfg.BACKEND),
          ("Core.Database",cfg.DATABASE),("Core.Infra",cfg.INFRA),("",""),
          ("Grid.Mail",cfg.MAIL),("Grid.Portfolio",cfg.PORTFOLIO),("Grid.LinkedIn",cfg.LINKEDIN),
          ("Grid.GitHub",cfg.USERNAME),("Grid.Facebook",cfg.FACEBOOK)]
    for l,v in rows:
        if not l: yy+=step//2; continue
        d.text((x0,yy),l,font=font,fill=chrome)
        w_=d.textlength(v,font=font); d.text((cfg.W-pad-w_,yy),v,font=font,fill=fg); yy+=step
    im.save(f"build/qa_{tag}.png"); print(f"build/qa_{tag}.png  ({len(xs)} dots)")

for dm in (True,False): render(dm)
