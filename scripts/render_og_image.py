#!/usr/bin/env python3
"""Render the default share card to og.png (1200x630).

Not part of the site build. build.py stays dependency-free and just links
the committed PNG. Re-run this only when the card artwork should change.

Requires Pillow and a serif/sans font. System paths below are tried in order.
  python3 scripts/render_og_image.py
"""
import os, sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit('Pillow is required to regenerate og.png (pip install pillow). The committed PNG is what the site uses.')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'og.png')
W, H = 1200, 630

BG = (255, 253, 249, 255)
TEXT = (29, 28, 26, 255)
MUTED = (108, 104, 98, 255)
ACCENT = (184, 67, 27, 255)
LINE = (231, 227, 220, 255)
GLOW = (255, 217, 194)  # #ffd9c2, the home-page wash

SERIF = [
    '/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
    '/Library/Fonts/Georgia.ttf',
]
SERIF_BOLD = [
    '/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
    '/Library/Fonts/Georgia Bold.ttf',
]
SERIF_ITALIC = [
    '/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf',
    '/Library/Fonts/Georgia Italic.ttf',
]
SANS = [
    '/usr/share/fonts/truetype/macos/Inter-Medium.ttf',
    '/usr/share/fonts/truetype/noto/NotoSans-Medium.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
]


def font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    sys.exit('No font found among:\n  ' + '\n  '.join(paths))


def glow(base):
    """Soft wash in the top-right corner, matching the home page."""
    gw = gh = 180
    small = Image.new('L', (gw, gh), 0)
    px = small.load()
    for y in range(gh):
        for x in range(gw):
            dx, dy = x - gw / 2, y - gh / 2
            t = 1 - (dx * dx + dy * dy) ** 0.5 / (gw / 2)
            if t > 0:
                px[x, y] = int(255 * t * t)
    layer = Image.merge('RGBA', (
        Image.new('L', (gw, gh), GLOW[0]),
        Image.new('L', (gw, gh), GLOW[1]),
        Image.new('L', (gw, gh), GLOW[2]),
        small,
    )).resize((980, 980), Image.Resampling.LANCZOS)
    base.alpha_composite(layer, (W - 640, -280))


def main():
    img = Image.new('RGBA', (W, H), BG)
    glow(img)
    draw = ImageDraw.Draw(img)

    # Letterpress rule, so the card still reads when a preview sits on white.
    draw.rectangle([0, 0, W, 10], fill=ACCENT)

    mark = 84
    mx, my = 80, 108
    draw.rounded_rectangle([mx, my, mx + mark, my + mark], radius=18, fill=ACCENT)
    ol = font(SERIF_BOLD, 34)
    bb = ol.getbbox('OL')
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((mx + (mark - tw) / 2 - bb[0], my + (mark - th) / 2 - bb[1] - 1), 'OL', font=ol, fill=(255, 255, 255, 255))

    name = font(SERIF, 72)
    tag = font(SERIF_ITALIC, 34)
    url = font(SANS, 22)

    draw.text((80, 248), 'Omer Levi Hevroni', font=name, fill=TEXT)
    draw.text((80, 352), 'Writing on application security and AI agents.', font=tag, fill=MUTED)

    draw.rectangle([80, 520, 232, 523], fill=LINE)
    draw.text((80, 544), 'omerlh.github.io', font=url, fill=MUTED)

    rgb = Image.new('RGB', (W, H), (255, 253, 249))
    rgb.paste(img, mask=img.split()[-1])
    rgb.save(OUT, 'PNG', optimize=True)
    print(f'wrote {OUT} ({W}x{H}, {os.path.getsize(OUT)} bytes)')


if __name__ == '__main__':
    main()
