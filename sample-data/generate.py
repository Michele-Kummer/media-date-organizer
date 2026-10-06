"""Generate a tiny synthetic photo set for testing photo-date-fixer."""
import pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).parent / "2024-01-05"
ROOT.mkdir(parents=True, exist_ok=True)


def make_png_with_exif(path, color, dt_str):
    img = Image.new("RGB", (100, 100), color)
    exif = img.getexif()
    exif[0x0132] = dt_str
    sub = exif.get_ifd(0x8769)
    sub[0x9003] = dt_str
    sub[0x9004] = dt_str
    img.save(path, "PNG", exif=exif.tobytes())


def make_jpg_with_exif(path, color, dt_str):
    img = Image.new("RGB", (100, 100), color)
    exif = img.getexif()
    exif[0x0132] = dt_str
    sub = exif.get_ifd(0x8769)
    sub[0x9003] = dt_str
    sub[0x9004] = dt_str
    img.save(path, "JPEG", exif=exif.tobytes(), quality=90)


make_png_with_exif(ROOT / "sample_a.png", (120, 200, 240), "2024:01:05 10:00:00")
make_png_with_exif(ROOT / "sample_b.heic", (240, 180, 100), "2024:01:05 10:00:00")
make_jpg_with_exif(ROOT / "sample_c.png", (160, 240, 150), "2023:12:20 14:30:00")

print(f"Generated three sample files under {ROOT}")
