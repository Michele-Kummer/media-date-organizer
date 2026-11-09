"""Generate a synthetic photo and video folder that shows each problem
media-date-organizer fixes, then copy it and run the tool on the copy, so the
two can be compared side by side.

    py sample-data/generate.py                 # Before and After
    py sample-data/generate.py --before-only   # just Before
    py sample-data/generate.py --out D:\\Demo  # somewhere else

By default it writes "sample-data/Sample Pictures/Before" and ".../After"
(both ignored by git), plus "Comparison.md", which lists every file in each
with its real format and Date Taken. Existing Before and After folders are
moved into "Sample Pictures/_previous", never deleted.

Videos need ffmpeg (pip install "imageio-ffmpeg>=0.5"); without it they are
left out. Writing a video's date in After needs ExifTool.
"""
import argparse
import datetime
import os
import pathlib
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'skills' / 'media-date-organizer' / 'scripts'))
import organize  # noqa: E402

DEFAULT_OUT = HERE / 'Sample Pictures'

# The steps run on each year folder in After: the routine ones (--all), plus
# setting ads aside, moving each file into a folder named for its date, and
# then flattening the dated files up into the year folder itself
AFTER_FLAGS = ('--all', '--quarantine-ads', '--apply-moves', '--flatten', '--apply')

# Every sample: (path in Before, kind, Date Taken or None, label, colour).
# kind is the real content: jpeg, png, thumbnail, null (an all-zero copy),
# aae, appledouble, thumbsdb, video. The extension in the path may lie.
# Before holds year folders with day folders inside, like a real library.
D = datetime.datetime
SAMPLES = [
    # Date only in the name: Date Taken is written from it
    ('2024/2024-07-04/IMG_20240704_183012.jpg', 'jpeg', None, 'Date only in the name', (231, 111, 81)),
    # PNG: Explorer never shows its Date Taken, so it is converted to JPEG
    ('2024/2024-07-04/Fireworks.png', 'png', D(2024, 7, 4, 21, 15), 'PNG: Explorer hides the date', (38, 70, 83)),
    # Extension lies: really a JPEG
    ('2024/2024-07-04/Beach.PNG', 'jpeg', D(2024, 7, 4, 12, 0), 'Really a JPEG named .PNG', (42, 157, 143)),
    ('2024/2024-07-04/VID_20240704_201500.mp4', 'video', None, 'Video date only in the name', None),
    # A phone gallery's thumbnails, brought along by an import
    ('2024/2024-07-04/46.jpg', 'thumbnail', None, 'Phone thumbnail', (233, 196, 106)),
    ('2024/2024-07-04/47.jpg', 'thumbnail', None, 'Phone thumbnail', (244, 162, 97)),
    ('2024/2024-07-04/0c4cda27-b4cc-4e92-a446-d6b780f24a64.jpg', 'jpeg', None, 'App ad', (200, 200, 200)),
    # Imported on 2024-01-15 but taken on other days: moved to folders named
    # for their dates, then flattened into 2024 with the rest
    ('2024/2024-01-15/IMG_0412.JPG', 'jpeg', D(2024, 1, 1, 0, 5), 'Taken 2024-01-01, filed 2024-01-15', (192, 57, 43)),
    ('2024/2024-01-15/IMG_0412.AAE', 'aae', None, None, None),
    ('2024/2024-01-15/._IMG_0412.JPG', 'appledouble', None, None, None),
    ('2024/2024-01-15/Thumbs.db', 'thumbsdb', None, None, None),
    ('2024/2024-01-15/IMG_0413.HEIC', 'jpeg', D(2024, 1, 1, 10, 30), 'Really a JPEG named .HEIC', (39, 174, 96)),
    ('2024/2024-01-15/Screenshot_20240115-093000.png', 'png', None, 'Screenshot: date in the name', (52, 73, 94)),
    ('2024/2024-01-15/IMG_0420.jpg', 'null', None, None, None),
    ('2024/2024-01-15/32#xffa2defe.png', 'png', None, 'Colour swatch', (162, 222, 254)),
    ('2024/2024-01-15/clip.mp4', 'video', D(2024, 3, 10, 15, 0), 'Video filed under the wrong date', None),
    # Date only in the folder's name
    ('2023/Aug 19 2023/Party.jpg', 'jpeg', None, 'Date only in the folder name', (131, 56, 236)),
    ('2023/Aug 19 2023/Cake.jpg', 'jpeg', D(2023, 8, 19, 16, 45), 'Birthday cake', (214, 51, 132)),
    ('2023/Aug 19 2023/scribble2mammoth_over@2x.png', 'png', None, 'App button image', (255, 190, 11)),
]

AAE = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
       '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0"><dict>'
       '<key>adjustmentFormatIdentifier</key><string>com.apple.photo</string></dict></plist>\n')


def _picture(label: str, colour: tuple, size=(800, 600)) -> Image.Image:
    """A coloured picture with its label written large, so each sample is
    easy to tell apart in Explorer's thumbnails."""
    img = Image.new('RGB', size, colour)
    draw = ImageDraw.Draw(img)
    # Lighter bands so a shrunken copy still has detail
    for y in range(0, size[1], 40):
        draw.rectangle((0, y, size[0], y + 8), fill=tuple(min(255, c + 30) for c in colour))
    font = ImageFont.load_default(size=max(20, size[0] // 18))
    text = 'white' if sum(colour) < 450 else 'black'
    draw.multiline_text((size[0] // 2, size[1] // 2), label.replace(': ', ':\n'), fill=text,
                        font=font, anchor='mm', align='center')
    return img


def _exif(taken):
    exif = Image.Exif()
    if taken is not None:
        stamp = taken.strftime('%Y:%m:%d %H:%M:%S')
        exif[0x0132] = stamp
        sub = exif.get_ifd(0x8769)
        sub[0x9003] = stamp
        sub[0x9004] = stamp
    return exif


def _video(path: pathlib.Path, label: str, taken) -> bool:
    ffmpeg = organize._find_ffmpeg()
    if not ffmpeg:
        return False
    cmd = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi',
           '-i', 'testsrc=duration=3:size=640x360:rate=15', '-pix_fmt', 'yuv420p']
    if taken is not None:
        # Media Created is stored in UTC
        utc = taken.astimezone(datetime.timezone.utc)
        cmd += ['-metadata', 'creation_time=' + utc.strftime('%Y-%m-%dT%H:%M:%SZ')]
    else:
        cmd += ['-map_metadata', '-1']
    subprocess.run(cmd + ['-metadata', 'title=' + label, str(path)], check=True, capture_output=True)
    return True


def make_before(folder) -> list:
    """Write every sample into folder; return the paths left out (videos
    without ffmpeg)."""
    folder = pathlib.Path(folder)
    skipped = []
    for rel, kind, taken, label, colour in SAMPLES:
        path = folder / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if kind == 'jpeg':
            _picture(label, colour).save(path, 'JPEG', exif=_exif(taken), quality=90)
        elif kind == 'png':
            _picture(label, colour).save(path, 'PNG', exif=_exif(taken))
        elif kind == 'thumbnail':
            _picture(label, colour, size=(384, 512)).save(path, 'JPEG', quality=80)
        elif kind == 'null':
            # A copy that stopped before any data was written
            path.write_bytes(bytes(48_000))
        elif kind == 'aae':
            path.write_text(AAE, encoding='utf-8')
        elif kind == 'appledouble':
            path.write_bytes(organize.APPLEDOUBLE_MAGIC + b'\x00\x02\x00\x00' + bytes(4088))
        elif kind == 'thumbsdb':
            path.write_bytes(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + bytes(1016))
        elif kind == 'video':
            if not _video(path, label, taken):
                skipped.append(rel)
    return skipped


def _set_aside(folder: pathlib.Path) -> None:
    """Move an existing folder into _previous beside it, never deleting it."""
    if not folder.exists():
        return
    previous = folder.parent / '_previous'
    previous.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H%M%S')
    shutil.move(str(folder), str(previous / f'{folder.name} {stamp}'))


def make_after(before, after) -> tuple:
    """Copy before to after and run organize.py on each year folder in the
    copy, as on E:\\Pictures\\2024; return the highest exit code and the
    output of every run."""
    import contextlib
    import io
    shutil.copytree(before, after)
    worst, logs = 0, []
    for year in sorted(p for p in pathlib.Path(after).iterdir() if p.is_dir()):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = organize.main(['--root', str(year), *AFTER_FLAGS])
        worst = max(worst, code)
        logs.append(f'===== {year.name} (exit code {code}) =====\n{out.getvalue()}')
    return worst, '\n'.join(logs)


def describe(folder) -> list:
    """(path, real format, Date Taken) for every file in folder, sorted."""
    folder = pathlib.Path(folder)
    rows = []
    for path in sorted(p for p in folder.rglob('*') if p.is_file()):
        rel = path.relative_to(folder).as_posix()
        if path.suffix.lower() == '.xlsx':
            rows.append((rel, 'audit workbook', ''))
            continue
        kind = organize.detect_type(str(path))
        taken = None
        if kind:
            try:
                taken = organize.read_metadata(str(path), kind)['date_taken']
            except Exception:
                taken = None
        fmt = kind.lstrip('.').upper() if kind else 'not media'
        rows.append((rel, fmt, taken.strftime('%Y-%m-%d %H:%M') if taken else 'blank'))
    return rows


def comparison(before, after) -> str:
    lines = ['# Before and after', '',
             f'After is a copy of Before with `organize.py {" ".join(AFTER_FLAGS)}` run on each year folder.', '']
    for title, folder in (('Before', before), ('After', after)):
        if not pathlib.Path(folder).exists():
            continue
        lines += [f'## {title}', '', '| File | Real format | Date Taken |', '|---|---|---|']
        lines += [f'| `{rel}` | {fmt} | {taken} |' for rel, fmt, taken in describe(folder)]
        lines.append('')
    return '\n'.join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Generate sample photos and videos, before and after.')
    ap.add_argument('--out', default=str(DEFAULT_OUT), help='Folder to write Before and After into.')
    ap.add_argument('--before-only', action='store_true', help='Only write Before.')
    args = ap.parse_args(argv)

    out = pathlib.Path(args.out)
    before, after = out / 'Before', out / 'After'
    _set_aside(before)
    _set_aside(after)
    skipped = make_before(before)
    print(f'Wrote {len(SAMPLES) - len(skipped)} sample files to {before}')
    for rel in skipped:
        print(f'Left out {rel}: ffmpeg is needed for videos (pip install "imageio-ffmpeg>=0.5")')
    if not args.before_only:
        code, log = make_after(before, after)
        (out / 'After log.txt').write_text(log, encoding='utf-8')
        print(f'Ran organize.py on each year folder of a copy in {after} (exit code {code}); its output is in "After log.txt"')
        if code:
            return code
    (out / 'Comparison.md').write_text(comparison(before, after), encoding='utf-8')
    print(f'Listed every file with its format and Date Taken in {out / "Comparison.md"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
