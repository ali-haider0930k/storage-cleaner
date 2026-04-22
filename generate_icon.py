"""Generate icon.ico from a programmatically drawn image."""
import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("pillow not installed; skipping icon generation")
    sys.exit(0)


def draw_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    s = size
    # Rounded square backdrop with gradient feel
    pad = int(s * 0.08)
    corner = int(s * 0.20)
    d.rounded_rectangle(
        (pad, pad, s - pad, s - pad),
        radius=corner,
        fill=(15, 17, 21, 255),
        outline=(59, 130, 246, 255),
        width=max(1, int(s * 0.02)),
    )

    # Disk cylinder rings
    cx, cy = s // 2, s // 2
    r_outer = int(s * 0.30)
    r_inner = int(s * 0.12)
    # Outer ring
    d.ellipse(
        (cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer),
        outline=(59, 130, 246, 255),
        width=max(2, int(s * 0.03)),
    )
    # Middle ring
    r_mid = int(s * 0.21)
    d.ellipse(
        (cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid),
        outline=(34, 197, 94, 220),
        width=max(1, int(s * 0.022)),
    )
    # Inner dot
    d.ellipse(
        (cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner),
        fill=(59, 130, 246, 255),
    )
    # Small "spark" in the corner for the "clean" motif
    sx = int(s * 0.72)
    sy = int(s * 0.28)
    spark = int(s * 0.08)
    d.polygon(
        [
            (sx, sy - spark),
            (sx + spark * 0.35, sy - spark * 0.35),
            (sx + spark, sy),
            (sx + spark * 0.35, sy + spark * 0.35),
            (sx, sy + spark),
            (sx - spark * 0.35, sy + spark * 0.35),
            (sx - spark, sy),
            (sx - spark * 0.35, sy - spark * 0.35),
        ],
        fill=(34, 197, 94, 255),
    )
    return img


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [draw_icon(s) for s in sizes]
    target = os.path.join(here, "icon.ico")
    images[-1].save(target, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"Wrote {target} ({len(sizes)} sizes)")


if __name__ == "__main__":
    main()
