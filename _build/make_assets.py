#!/usr/bin/env python3
"""One-off: draws favicon.svg, favicon.ico, apple-touch-icon.png and og-image.png (original art, needs Pillow)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BG, TEAL, ICE, STEEL = (5, 13, 22), (63, 193, 201), (155, 231, 234), (143, 180, 200)

(ROOT / "favicon.svg").write_text("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#071622"/>
  <rect x="1" y="1" width="30" height="30" rx="5" fill="none" stroke="#3fc1c9" stroke-width="1.5"/>
  <path d="M16 6 C16 6 8.5 14.5 8.5 19.5 a7.5 7.5 0 0 0 15 0 C23.5 14.5 16 6 16 6 Z" fill="none" stroke="#9be7ea" stroke-width="1.8"/>
  <path d="M12.5 20 q3.5 -3 7 0" fill="none" stroke="#3fc1c9" stroke-width="1.6"/>
</svg>
""")


def icon(size):
    s = 8  # supersample
    N = size * s
    im = Image.new("RGB", (N, N), (7, 22, 34))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([N * .03, N * .03, N * .97, N * .97], radius=N * .17, outline=TEAL, width=max(2, N // 22))
    # droplet: circle + triangle
    cx, cy, r = N * .5, N * .6, N * .24
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ICE, width=max(2, N // 20))
    d.line([(cx - r * .93, cy - r * .35), (cx, N * .17), (cx + r * .93, cy - r * .35)], fill=ICE, width=max(2, N // 20), joint="curve")
    d.arc([cx - r * .55, cy - r * .1, cx + r * .55, cy + r * .5], 200, 340, fill=TEAL, width=max(2, N // 24))
    return im.resize((size, size), Image.LANCZOS)


icon(180).save(ROOT / "apple-touch-icon.png")
icon(256).save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])


def font(size, bold=True):
    for n in (("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), ("LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf")):
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


W, Hh = 1200, 630
og = Image.new("RGB", (W, Hh), BG)
d = ImageDraw.Draw(og)
for y in range(Hh):  # vertical water gradient
    t = y / Hh
    d.line([(0, y), (W, y)], fill=(int(5 + 6 * t), int(13 + 30 * (1 - abs(t - .55))), int(22 + 40 * (1 - abs(t - .55)))))
# ground + water table + casing + pump + tank (line art, right side)
d.line([(560, 190), (W, 190)], fill=STEEL, width=2)
for x in range(792, W, 24):
    d.arc([x, 336, x + 24, 356], 180 if (x // 24) % 2 else 0, 360 if (x // 24) % 2 else 180, fill=TEAL, width=2)
d.line([(900, 170), (900, 590)], fill=ICE, width=4)
d.line([(990, 170), (990, 590)], fill=ICE, width=4)
d.line([(880, 170), (1010, 170)], fill=ICE, width=4)
d.line([(945, 170), (945, 470)], fill=TEAL, width=4)
d.rounded_rectangle([922, 470, 968, 545], radius=8, outline=TEAL, width=4)
d.line([(922, 495), (968, 495)], fill=TEAL, width=2)
d.line([(922, 515), (968, 515)], fill=TEAL, width=2)
d.line([(945, 230), (740, 230)], fill=TEAL, width=4)
d.rounded_rectangle([650, 70, 830, 215], radius=70, outline=ICE, width=4)
d.line([(740, 215), (740, 230)], fill=TEAL, width=4)
d.ellipse([590, 110, 630, 150], outline=TEAL, width=4)
d.line([(630, 130), (650, 130)], fill=TEAL, width=3)
d.line([(610, 130), (622, 118)], fill=TEAL, width=3)
d.text((60, 190), "Well Pump", font=font(92), fill=(233, 243, 248))
d.text((60, 295), "Reference Library", font=font(70), fill=ICE)
d.text((62, 400), "Pumps · tanks · controls · sizing · compare", font=font(32, False), fill=STEEL)
d.text((62, 450), "Free and ad-free", font=font(32, False), fill=TEAL)
d.text((62, 560), "wellpumpchart.pages.dev", font=font(28, False), fill=STEEL)
og.save(ROOT / "og-image.png")
print("assets written")
