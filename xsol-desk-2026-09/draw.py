"""Drawing helpers for the desk renderer, plus one palette.

Extracted so the renderer stands alone: a supersampled pen over Pillow, a font
loader, and a single colour set. Nothing else in the project reads colour, so
swapping the values below is the whole theming story.
"""
import math

from PIL import ImageFont

# One palette. Replace these values with your own.
PALETTE = dict(
    BG=(7, 7, 8), HAIR=(24, 22, 23), BORDER=(38, 34, 35), DIM=(76, 70, 68),
    SECOND=(120, 112, 106), PRIMARY=(210, 203, 192), BRIGHT=(240, 234, 224),
    ACCENT=(210, 34, 34), ACCENT_DIM=(62, 18, 18),
    COUNTER=(216, 207, 190), COUNTER_DIM=(70, 65, 57), FILL=(28, 12, 12),
)
globals().update(PALETTE)   # the pen takes a few of these as argument defaults


def palette(_name=None):
    return PALETTE


SS = 2                                   # supersample factor, downscaled at the end
MENLO = "/System/Library/Fonts/Menlo.ttc"

def F(size, bold=False, italic=False):
    idx = 3 if (bold and italic) else 2 if italic else 1 if bold else 0
    return ImageFont.truetype(MENLO, size * SS, index=idx)


class Pen:
    """Thin wrapper so all coordinates are written in final-frame pixels."""
    def __init__(self, d):
        self.d = d

    def text(self, xy, s, font, fill, anchor="lt", spacing=0):
        x, y = xy[0] * SS, xy[1] * SS
        if spacing:
            for ch in s:
                self.d.text((x, y), ch, font=font, fill=fill, anchor=anchor)
                x += self.d.textlength(ch, font=font) + spacing * SS
        else:
            self.d.text((x, y), s, font=font, fill=fill, anchor=anchor)

    def line(self, pts, fill, width=1):
        self.d.line([(p[0] * SS, p[1] * SS) for p in pts], fill=fill,
                    width=max(1, int(width * SS)), joint="curve")

    def rect(self, box, outline=None, fill=None, width=1):
        x0, y0, x1, y1 = [v * SS for v in box]
        self.d.rectangle([x0, y0, x1, y1], outline=outline, fill=fill,
                         width=max(1, int(width * SS)))

    def dot(self, xy, r, fill):
        x, y = xy[0] * SS, xy[1] * SS
        rr = r * SS
        self.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=fill)

    def poly(self, pts, fill):
        """Filled polygon in final-frame pixels. Added 2026-09-14 for area fills."""
        self.d.polygon([(p[0] * SS, p[1] * SS) for p in pts], fill=fill)

    def dashed(self, p0, p1, fill, width=1, dash=7, gap=6):
        x0, y0 = p0; x1, y1 = p1
        L = math.hypot(x1 - x0, y1 - y0)
        if L <= 0: return
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        t = 0.0
        while t < L:
            a = (x0 + ux * t, y0 + uy * t)
            b = (x0 + ux * min(t + dash, L), y0 + uy * min(t + dash, L))
            self.line([a, b], fill, width)
            t += dash + gap

    def brackets(self, box, size=14, fill=BORDER, width=1):
        x0, y0, x1, y1 = box
        for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1),
                                 (x0, y1, 1, -1), (x1, y1, -1, -1)):
            self.line([(cx, cy), (cx + dx * size, cy)], fill, width)
            self.line([(cx, cy), (cx, cy + dy * size)], fill, width)
