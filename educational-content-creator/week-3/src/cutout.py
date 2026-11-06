"""Transparent presenter cut-outs for thumbnails (same character as the videos), with chosen expressions."""
import sys
sys.path.insert(0, "src")
from PIL import Image
from presenter import body, head_base, features
def cutout(openness=.6, wide=.6, brow=1.0, s=1.0, out="build/cutout.png"):
    im = Image.new("RGBA", (int(900 * s), int(1300 * s)), (0, 0, 0, 0))
    bd = body(s).resize((int(900 * s), int(1400 * s)), Image.LANCZOS); im.alpha_composite(bd.crop((0, 0, im.width, im.height)), (0, int(110 * s)))
    hb = head_base(s); hb.alpha_composite(features(s, openness, wide, 0, brow)); hb = hb.resize((int(560 * s), int(640 * s)), Image.LANCZOS)
    im.alpha_composite(hb, (int(170 * s), int(170 * s))); im = im.crop(im.getbbox()); im.save(out); return out
if __name__ == "__main__":
    cutout(.75, .3, 1.0, out="build/cut_surprised.png"); cutout(.35, 1.0, .6, out="build/cut_smile.png"); cutout(.0, .5, .2, out="build/cut_neutral.png")
