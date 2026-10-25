"""Generate Android launcher icons at standard densities."""
from PIL import Image, ImageDraw, ImageFont
import os

APP_RES = "/home/z/my-project/android-app/res"
BG = (8, 7, 13)
GRAD_START = (217, 70, 239)
GRAD_MID = (139, 92, 246)
GRAD_END = (34, 211, 238)

DENSITIES = {"mipmap-mdpi": 48, "mipmap-hdpi": 72, "mipmap-xhdpi": 96, "mipmap-xxhdpi": 144, "mipmap-xxxhdpi": 192}
FOREGROUND_DENSITIES = {"mipmap-mdpi": 108, "mipmap-hdpi": 162, "mipmap-xhdpi": 216, "mipmap-xxhdpi": 324, "mipmap-xxxhdpi": 432}


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_gradient(size):
    img = Image.new("RGB", (size, size), BG)
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            if t < 0.5:
                c = lerp(GRAD_START, GRAD_MID, t * 2)
            else:
                c = lerp(GRAD_MID, GRAD_END, (t - 0.5) * 2)
            px[x, y] = c
    return img


def find_font(size_px):
    for c in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        if os.path.exists(c):
            return ImageFont.truetype(c, size_px)
    return ImageFont.load_default()


def rounded_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def make_launcher_icon(size, out_path):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad = make_gradient(size)
    ring_mask = rounded_mask(size, int(size * 0.22))
    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ring.paste(grad, (0, 0), ring_mask)
    img = Image.alpha_composite(img, ring)
    inner_size = int(size * 0.72)
    inner_off = (size - inner_size) // 2
    inner = Image.new("RGBA", (inner_size, inner_size), (0, 0, 0, 0))
    id_ = ImageDraw.Draw(inner)
    id_.rounded_rectangle([0, 0, inner_size - 1, inner_size - 1], radius=int(inner_size * 0.20), fill=BG + (255,))
    img.paste(inner, (inner_off, inner_off), inner)
    d = ImageDraw.Draw(img)
    font = find_font(int(size * 0.34))
    text = "RS"
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1]
    grad_text = make_gradient(size)
    alpha = Image.new("L", (size, size), 0)
    ad = ImageDraw.Draw(alpha)
    ad.text((tx, ty), text, font=font, fill=255)
    grad_text.putalpha(alpha)
    img = Image.alpha_composite(img, grad_text)
    img.save(out_path, "PNG")


def make_foreground(size, out_path):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = find_font(int(size * 0.42))
    text = "RS"
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1]
    grad = make_gradient(size)
    alpha = Image.new("L", (size, size), 0)
    ad = ImageDraw.Draw(alpha)
    ad.text((tx, ty), text, font=font, fill=255)
    grad.putalpha(alpha)
    img = Image.alpha_composite(img, grad)
    img.save(out_path, "PNG")


print("Generating launcher icons:")
for folder, size in DENSITIES.items():
    out_dir = os.path.join(APP_RES, folder)
    os.makedirs(out_dir, exist_ok=True)
    make_launcher_icon(size, os.path.join(out_dir, "ic_launcher.png"))
    make_launcher_icon(size, os.path.join(out_dir, "ic_launcher_round.png"))

print("Generating adaptive foreground icons:")
for folder, size in FOREGROUND_DENSITIES.items():
    out_dir = os.path.join(APP_RES, folder)
    os.makedirs(out_dir, exist_ok=True)
    make_foreground(size, os.path.join(out_dir, "ic_launcher_foreground.png"))

print("All Android icons generated.")
