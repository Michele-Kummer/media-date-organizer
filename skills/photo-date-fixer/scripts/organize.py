#!/usr/bin/env python3
"""
organize.py — read photo metadata (EXIF, MOV mvhd, HEIC TIFF) and sort files
by real Date Taken.

Phases (several can be given on one command line; they run in a fixed order
and a summary of every phase's counts and problems is printed at the end):
    --all               Shorthand for --delete-aae --fill-blanks --convert-png
                        --apply-moves --sync-timestamps. Add --move-no-data,
                        --quarantine-ads or --flatten to include those too.
    --delete-aae        Permanently delete every .AAE file in the root folder
                        and every subfolder. These are the edit-instruction
                        sidecars iPhones export next to a photo; they hold no
                        image and nothing on Windows reads them. Add --dry-run
                        to list them without deleting anything.
    --report-only       Scan and write audit XLSX; make no changes.
    --fill-blanks       Write DateTimeOriginal into EXIF for JPEG/PNG files that
                        are missing Date Taken. Uses a date embedded in the
                        filename (e.g. 2023-12-20_<id>-main.jpg,
                        IMG_20231220_142355.jpg) first, then the containing
                        folder's YYYY-MM-DD name at 12:00:00. The file's
                        modified time is never used — it is usually the import
                        time. JPEGs are rewritten without re-encoding. HEIC
                        and video files are written with exiftool when it is
                        installed, else flagged. Empty (0-byte) files are
                        skipped and counted.
    --convert-png       Re-encode PNG files as JPEG at quality 95, preserving
                        EXIF. Leaves originals in place. PNGs with any
                        transparent pixels are skipped and stay PNG, as are
                        "-overlay" PNGs (Snapchat caption layers).
    --apply-moves       Move files whose Date Taken does not match their current
                        folder name into a sibling folder named for the real
                        date. Renames use the clean iPhone-native stem; a
                        _<folder-date> suffix is appended only if Date Taken is
                        blank AND the folder is a dated folder.
    --sync-timestamps   Set each file's "Date Modified" and "Date Created" to
                        its EXIF Date Taken, BUT only for files that appear to
                        be unedited (EXIF ModifyDate equals DateTimeOriginal
                        and no editor-software tag is present). Date Created
                        is only settable on Windows; elsewhere just Date
                        Modified is synced.
    --flatten           Move every file that has a Date Taken out of its
                        subfolder and up into the root folder itself, then
                        delete the subfolders left empty. Files with no Date
                        Taken stay where they are (the folder name may be the
                        only record of their date), so their folders survive.
                        A name already taken in the root gets a _<date-taken>
                        suffix. Add --dry-run to preview without changing
                        anything.
    --quarantine-ads    Move ad images into an _ads folder inside the root,
                        keeping their subfolder path, for the user to review
                        and delete. A file is an ad only if BOTH hold: its
                        name is a UUID (0c4cda27-b4cc-4e92-a446-d6b780f24a64),
                        a 9-character hex id plus a number (bed51b94a_1595),
                        or gmsnet plus an optional number (gmsnet2); AND it
                        carries no camera Make/Model. Name matches that do
                        have camera info are kept and listed. Looks in the
                        root folder and every subfolder. Nothing is deleted.
                        Add --dry-run to preview without moving anything.
    --move-no-data      Move media files that hold no image data (0 bytes, or
                        nothing but null bytes: the remains of a failed copy
                        or transfer) into a "_no-image-data" folder inside the
                        root, keeping their subfolder path. Looks in the root
                        folder and every subfolder. Nothing is deleted. Add
                        --dry-run to preview without moving anything.

Dependencies: Pillow (`pip install pillow`) and, for the audit workbook,
openpyxl (`pip install openpyxl`). Scanning works without openpyxl — the XLSX
step is skipped with a clear message if it's missing. exiftool is optional:
when present (on PATH, or in winget's default folder) --fill-blanks uses it
for HEIC and video files. Install with `winget install OliverBetz.ExifTool`.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
from collections import Counter
from typing import Optional

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("WARNING: Pillow is not installed. Install with: pip install pillow", file=sys.stderr)


# ---------------- Format detection ----------------

def detect_type(path: str) -> Optional[str]:
    """Return the canonical lowercase extension (with dot) or None."""
    try:
        with open(path, 'rb') as f:
            h = f.read(16)
    except OSError:
        return None
    if len(h) < 12:
        return None
    if h[:8] == b'\x89PNG\r\n\x1a\n':
        return '.png'
    if h[:3] == b'\xff\xd8\xff':
        return '.jpg'
    if h[:4] == b'GIF8':
        return '.gif'
    if h[:2] == b'BM':
        return '.bmp'
    if h[:4] in (b'II*\x00', b'MM\x00*'):
        return '.tif'
    if h[4:8] == b'ftyp':
        brand = h[8:12]
        if brand in (b'heic', b'heix', b'mif1', b'msf1'):
            return '.heic'
        if brand == b'qt  ':
            return '.mov'
        if brand in (b'mp42', b'mp41', b'isom'):
            return '.mp4'
        if brand.startswith(b'M4V'):
            return '.m4v'
        return '.mp4'
    if h[:4] == b'RIFF' and h[8:12] == b'WEBP':
        return '.webp'
    return None


# ---------------- Date Taken extraction ----------------

def _heic_dates(path: str) -> dict:
    """Return {DateTimeOriginal, DateTimeDigitized, DateTime, Software, Make,
    Model} strings found in a HEIC/HEIF file's embedded TIFF/EXIF block."""
    out = {}
    with open(path, 'rb') as f:
        data = f.read()
    for pat, endian in ((b'II*\x00', '<'), (b'MM\x00*', '>')):
        start = 0
        while True:
            i = data.find(pat, start)
            if i < 0:
                break
            start = i + 1
            try:
                ifd0 = struct.unpack(endian + 'I', data[i + 4:i + 8])[0]
                nentries = struct.unpack(endian + 'H', data[i + ifd0:i + ifd0 + 2])[0]
                if not (0 < nentries < 200):
                    continue
                for k in range(nentries):
                    e = i + ifd0 + 2 + k * 12
                    tag, typ, cnt = struct.unpack(endian + 'HHI', data[e:e + 8])
                    val_off = struct.unpack(endian + 'I', data[e + 8:e + 12])[0]
                    if tag == 0x0132 and typ == 2 and cnt < 32:
                        out['DateTime'] = data[i + val_off:i + val_off + cnt].rstrip(b'\x00').decode('ascii', 'replace')
                    if tag == 0x0131 and typ == 2 and cnt < 128:
                        out['Software'] = data[i + val_off:i + val_off + cnt].rstrip(b'\x00').decode('ascii', 'replace')
                    if tag in (0x010F, 0x0110) and typ == 2 and 4 < cnt < 128:
                        out['Make' if tag == 0x010F else 'Model'] = data[i + val_off:i + val_off + cnt].rstrip(b'\x00').decode('ascii', 'replace')
                    if tag == 0x8769:
                        sn = struct.unpack(endian + 'H', data[i + val_off:i + val_off + 2])[0]
                        for kk in range(sn):
                            se = i + val_off + 2 + kk * 12
                            stag, styp, scnt = struct.unpack(endian + 'HHI', data[se:se + 8])
                            svo = struct.unpack(endian + 'I', data[se + 8:se + 12])[0]
                            if stag == 0x9003 and styp == 2 and scnt < 32:
                                out['DateTimeOriginal'] = data[i + svo:i + svo + scnt].rstrip(b'\x00').decode('ascii', 'replace')
                            if stag == 0x9004 and styp == 2 and scnt < 32:
                                out['DateTimeDigitized'] = data[i + svo:i + svo + scnt].rstrip(b'\x00').decode('ascii', 'replace')
                if out:
                    return out
            except Exception:
                continue
    return out


def _parse_exif_dt(s: str) -> Optional[datetime.datetime]:
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s.strip(), "%Y:%m:%d %H:%M:%S")
    except (ValueError, AttributeError):
        return None


def _mp4_times(path: str) -> dict:
    """Return {creation_time, modification_time} from the mvhd atom, plus
    {camera} when the file carries a device-make tag."""
    out = {}
    with open(path, 'rb') as f:
        data = f.read()
    for marker in (b'com.apple.quicktime.make', b'\xa9mak', b'com.android.manufacturer'):
        if marker in data:
            out['camera'] = marker.decode('latin-1')
            break
    i = data.find(b'mvhd')
    if i < 0:
        return out
    p = data[i + 4:]
    try:
        if p[0] == 1:
            ct = struct.unpack('>Q', p[4:12])[0]
            mt = struct.unpack('>Q', p[12:20])[0]
        else:
            ct = struct.unpack('>I', p[4:8])[0]
            mt = struct.unpack('>I', p[8:12])[0]
        epoch = datetime.datetime(1904, 1, 1)
        for key, v in (('creation_time', ct), ('modification_time', mt)):
            dt = epoch + datetime.timedelta(seconds=v)
            if dt.year > 1970:
                out[key] = dt
    except Exception:
        pass
    return out


def _pil_meta(path: str) -> dict:
    """Return {DateTimeOriginal, DateTime, Software, Make, Model} from an
    image via Pillow."""
    out = {}
    if not HAS_PIL:
        return out
    try:
        img = Image.open(path)
        exif = img.getexif()
        v = exif.get_ifd(0x8769).get(0x9003)
        if v:
            out['DateTimeOriginal'] = v
        v = exif.get(0x0132)
        if v:
            out['DateTime'] = v
        v = exif.get(0x0131)
        if v:
            out['Software'] = v
        v = exif.get(0x010F)
        if v:
            out['Make'] = v
        v = exif.get(0x0110)
        if v:
            out['Model'] = v
    except Exception:
        pass
    return out


def _camera(d: dict) -> Optional[str]:
    """Join EXIF Make and Model into one string, or None if both are blank."""
    parts = [str(d.get(k) or '').strip('\x00 ') for k in ('Make', 'Model')]
    return ' '.join(p for p in parts if p) or None


def read_metadata(path: str, ftype: str) -> dict:
    """Return a normalized dict of {date_taken, modify_time, software, camera}."""
    out = {'date_taken': None, 'modify_time': None, 'software': None, 'camera': None}
    if ftype == '.heic':
        d = _heic_dates(path)
        out['date_taken'] = _parse_exif_dt(d.get('DateTimeOriginal') or d.get('DateTimeDigitized'))
        out['modify_time'] = _parse_exif_dt(d.get('DateTime'))
        out['software'] = d.get('Software')
        out['camera'] = _camera(d)
    elif ftype in ('.mov', '.mp4', '.m4v'):
        d = _mp4_times(path)
        out['date_taken'] = d.get('creation_time')
        out['modify_time'] = d.get('modification_time')
        out['camera'] = d.get('camera')
    elif ftype in ('.png', '.jpg', '.jpeg', '.tif', '.tiff'):
        d = _pil_meta(path)
        if not d and ftype in ('.tif', '.tiff'):
            # TIFF variants Pillow cannot open: walk the TIFF structure directly
            d = _heic_dates(path)
        out['date_taken'] = _parse_exif_dt(d.get('DateTimeOriginal'))
        out['modify_time'] = _parse_exif_dt(d.get('DateTime'))
        out['software'] = d.get('Software')
        out['camera'] = _camera(d)
    elif ftype == '.webp':
        out['camera'] = _camera(_pil_meta(path))
    return out


# ---------------- Core workflow ----------------

MEDIA_EXTS = {'.png', '.jpg', '.jpeg', '.heic', '.heif', '.mov', '.mp4', '.m4v',
              '.tif', '.tiff', '.gif', '.bmp', '.webp'}

# Folder inside root that --quarantine-ads moves ad images into. Every phase
# ignores it.
QUARANTINE_DIR = '_ads'

# Folder inside root that --move-no-data moves empty / null-filled files into.
# Every phase ignores it.
NO_DATA_DIR = '_no-image-data'

HOLDING_DIRS = (QUARANTINE_DIR, NO_DATA_DIR)


def _prune_holding(root: str, dirpath: str, dirs: list) -> None:
    """Stop an os.walk of root from descending into the holding folders."""
    if dirpath == root:
        dirs[:] = [d for d in dirs if d not in HOLDING_DIRS]


def iter_media(root: str):
    """Yield (folder_name, filename, full_path) for every media file under root."""
    for folder in sorted(os.listdir(root)):
        fp = os.path.join(root, folder)
        if not os.path.isdir(fp) or folder in HOLDING_DIRS:
            continue
        for name in sorted(os.listdir(fp)):
            full = os.path.join(fp, name)
            if not os.path.isfile(full):
                continue
            ext = pathlib.Path(name).suffix.lower()
            if ext not in MEDIA_EXTS:
                continue
            yield folder, name, full


# YYYY-MM-DD or YYYYMMDD, optionally followed by HHMMSS, not embedded in a
# longer run of digits (so "Snapchat-1234567890" does not match).
_NAME_DATE_RE = re.compile(
    r'(?<!\d)(\d{4})([-_.]?)(\d{2})\2(\d{2})'
    r'(?:[-_ T.]?(\d{2})[-_.]?(\d{2})[-_.]?(\d{2})(?![0-9A-Za-z]))?(?!\d)')


def _filename_date(stem: str) -> Optional[datetime.datetime]:
    """Return the first plausible date embedded in a filename stem, at the
    embedded time if there is one, else 12:00:00."""
    today = datetime.date.today()
    for m in _NAME_DATE_RE.finditer(stem):
        try:
            d = datetime.date(int(m[1]), int(m[3]), int(m[4]))
        except ValueError:
            continue
        if d.year < 1990 or d > today:
            continue
        if m[5]:
            try:
                return datetime.datetime.combine(d, datetime.time(int(m[5]), int(m[6]), int(m[7])))
            except ValueError:
                pass
        return datetime.datetime.combine(d, datetime.time(12, 0, 0))
    return None


def _fallback_date(name: str, folder: str) -> tuple:
    """Return (datetime, source) to use when Date Taken is blank: the date in
    the filename, else the YYYY-MM-DD folder name at 12:00:00. The file's
    modified time is deliberately not consulted — imports reset it."""
    dt = _filename_date(pathlib.Path(name).stem)
    if dt is not None:
        return dt, 'filename'
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', folder)
    if m:
        return datetime.datetime(int(m[1]), int(m[2]), int(m[3]), 12, 0, 0), 'folder'
    return None, None


def scan(root: str) -> list:
    """Return a list of plan dicts for every file under root."""
    rows = []
    for folder, name, full in iter_media(root):
        m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', folder)
        folder_date = datetime.date(int(m[1]), int(m[2]), int(m[3])) if m else None
        ftype = detect_type(full) or pathlib.Path(name).suffix.lower()
        meta = read_metadata(full, ftype)
        dt = meta['date_taken']
        stem = pathlib.Path(name).stem
        base = re.match(r'^(.+?)_\d{4}-\d{2}-\d{2}$', stem)
        base = base.group(1) if base else stem
        ext_canonical = ftype.upper() if ftype else pathlib.Path(name).suffix
        fallback_source = _fallback_date(name, folder)[1] if dt is None else None
        if fallback_source == 'filename':
            action = 'fill-blank'
            target_folder = folder
            new_name = name
        elif fallback_source == 'folder':
            action = 'fill-blank'
            target_folder = folder
            new_name = f"{base}_{folder_date.isoformat()}{ext_canonical}"
        elif dt is None:
            action = 'skip-no-folder-date'
            target_folder = folder
            new_name = name
        elif folder_date is None or dt.date() == folder_date:
            action = 'keep'
            target_folder = folder
            new_name = f"{base}{ext_canonical}"
        else:
            action = 'move'
            target_folder = dt.date().isoformat()
            new_name = f"{base}{ext_canonical}"
        rows.append({
            'current_folder': folder,
            'current_name': name,
            'detected_type': (ftype or '').lstrip('.').upper(),
            'date_taken': dt.strftime('%Y-%m-%d %H:%M:%S') if dt else '',
            'target_folder': target_folder,
            'new_name': new_name,
            'action': action,
        })
    return rows


# ---------------- Apply moves ----------------

def apply_moves(root: str, plan: list) -> dict:
    """Execute moves and renames. Skips 'fill-blank' rows — those are handled
    by --fill-blanks separately."""
    counts = Counter()
    for r in plan:
        if r['action'] not in ('move', 'keep'):
            counts['skipped-' + r['action']] += 1
            continue
        src = os.path.join(root, r['current_folder'], r['current_name'])
        if not os.path.isfile(src):
            counts['missing'] += 1
            continue
        tgt_dir = os.path.join(root, r['target_folder'])
        os.makedirs(tgt_dir, exist_ok=True)
        dst = os.path.join(tgt_dir, r['new_name'])
        if src == dst:
            counts['unchanged'] += 1
            continue
        # A case-only rename (IMG_1.jpg -> IMG_1.JPG) "exists" on Windows but
        # is the same file, not a collision
        if os.path.exists(dst) and not os.path.samefile(src, dst):
            counts['collision'] += 1
            print(f"COLLISION, skipping: {dst}", file=sys.stderr)
            continue
        shutil.move(src, dst)
        counts[r['action']] += 1
    return dict(counts)


# ---------------- Fill blank Date Taken ----------------

def _jpeg_set_exif(path: str, exif_bytes: bytes) -> None:
    """Replace (or insert) the EXIF APP1 segment of a JPEG, leaving the
    compressed image data byte-for-byte untouched."""
    if len(exif_bytes) > 65533:
        raise ValueError("EXIF block too large for a JPEG APP1 segment")
    with open(path, 'rb') as f:
        data = f.read()
    if data[:2] != b'\xff\xd8':
        raise ValueError("not a JPEG file")
    pos = insert_at = 2
    old = []
    while pos + 4 <= len(data) and data[pos] == 0xFF:
        marker = data[pos + 1]
        if marker in (0xDA, 0xD9):  # start of scan / end of image
            break
        end = pos + 2 + struct.unpack('>H', data[pos + 2:pos + 4])[0]
        if marker == 0xE0 and pos == insert_at:
            insert_at = end  # keep JFIF header(s) first
        elif marker == 0xE1 and data[pos + 4:pos + 10] == b'Exif\x00\x00':
            old.append((pos, end))
        pos = end
    segment = b'\xff\xe1' + struct.pack('>H', len(exif_bytes) + 2) + exif_bytes
    out = bytearray(data[:insert_at]) + segment
    cur = insert_at
    for s, e in old:
        out += data[cur:s]
        cur = e
    out += data[cur:]
    tmp = path + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(out)
    os.replace(tmp, path)


def _write_exif_date_image(path: str, dt: datetime.datetime) -> None:
    """Write EXIF DateTime/DateTimeOriginal/DateTimeDigitized on JPEG or PNG.
    JPEGs get the EXIF segment swapped in place (no re-encode, no quality
    loss); other formats are re-saved through Pillow."""
    if not HAS_PIL:
        raise RuntimeError("Pillow is required to write EXIF; pip install pillow")
    ds = dt.strftime("%Y:%m:%d %H:%M:%S")
    tmp = path + '.tmp'
    with Image.open(path) as img:
        fmt = (img.format or '').upper()
        exif = img.getexif()
        exif[0x0132] = ds
        sub = exif.get_ifd(0x8769)
        sub[0x9003] = ds
        sub[0x9004] = ds
        exif_bytes = exif.tobytes()
        if fmt not in ('JPEG', 'MPO'):
            img.load()
            save_kwargs = {'exif': exif_bytes}
            if 'icc_profile' in img.info:
                save_kwargs['icc_profile'] = img.info['icc_profile']
            img.save(tmp, format=fmt, **save_kwargs)
    if fmt in ('JPEG', 'MPO'):
        _jpeg_set_exif(path, exif_bytes)
    else:
        os.replace(tmp, path)


def _find_exiftool() -> Optional[str]:
    """Return the path to exiftool, or None if it is not installed."""
    exe = shutil.which('exiftool')
    if exe:
        return exe
    # winget's default location, for terminals opened before it was on PATH
    local = os.environ.get('LOCALAPPDATA')
    if local:
        exe = os.path.join(local, 'Programs', 'ExifTool', 'ExifTool.exe')
        if os.path.isfile(exe):
            return exe
    return None


VIDEO_EXTS = ('.mov', '.mp4', '.m4v')


def _write_date_exiftool(exiftool: str, path: str, ftype: str, dt: datetime.datetime) -> None:
    """Write Date Taken with exiftool, for formats Pillow cannot write
    (HEIC, video). The file is rewritten in place; image data is not
    re-encoded."""
    ds = dt.strftime("%Y:%m:%d %H:%M:%S")
    if ftype in VIDEO_EXTS:
        tags = ['-QuickTime:CreateDate=' + ds, '-QuickTime:ModifyDate=' + ds,
                '-TrackCreateDate=' + ds, '-MediaCreateDate=' + ds]
    else:
        tags = ['-AllDates=' + ds]
    r = subprocess.run(
        [exiftool, '-charset', 'filename=utf8', '-overwrite_original', '-m', *tags, path],
        capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0 or '1 image files updated' not in r.stdout:
        msg = (r.stderr or r.stdout).strip().splitlines()
        raise RuntimeError(msg[-1] if msg else f"exiftool exited {r.returncode}")


def fill_blanks(root: str) -> dict:
    counts = Counter()
    exiftool = _find_exiftool()
    for folder, name, full in iter_media(root):
        if os.path.getsize(full) == 0:
            # A failed copy or transfer: there is no image to write a date into
            counts['empty-file'] += 1
            continue
        ftype = detect_type(full) or pathlib.Path(name).suffix.lower()
        meta = read_metadata(full, ftype)
        if meta['date_taken'] is not None:
            counts['already-dated'] += 1
            continue
        fill_dt, source = _fallback_date(name, folder)
        if fill_dt is None:
            counts['no-date-source'] += 1
            continue
        if ftype in ('.jpg', '.jpeg', '.png', '.tif', '.tiff'):
            try:
                try:
                    _write_exif_date_image(full, fill_dt)
                except Exception:
                    # e.g. a TIFF variant Pillow cannot open
                    if not exiftool:
                        raise
                    _write_date_exiftool(exiftool, full, ftype, fill_dt)
                counts['written-from-' + source] += 1
                print(f"WROTE Date Taken {fill_dt:%Y-%m-%d %H:%M:%S} (from {source}): {folder}/{name}")
            except Exception as e:
                counts['write-failed'] += 1
                print(f"FAILED to write {folder}/{name}: {e}", file=sys.stderr)
        elif ftype in ('.heic', '.heif') + VIDEO_EXTS:
            if not exiftool:
                counts['heic-mov-needs-exiftool'] += 1
                print(f"SKIPPED (needs exiftool): {folder}/{name}", file=sys.stderr)
                continue
            try:
                _write_date_exiftool(exiftool, full, ftype, fill_dt)
                counts['written-from-' + source] += 1
                print(f"WROTE Date Taken {fill_dt:%Y-%m-%d %H:%M:%S} (from {source}, exiftool): {folder}/{name}")
            except Exception as e:
                counts['write-failed'] += 1
                print(f"FAILED to write {folder}/{name}: {e}", file=sys.stderr)
        else:
            # GIF, BMP, WEBP: no Date Taken field this script can write
            counts['unsupported-format'] += 1
    if counts['empty-file']:
        print(f"NOTE: {counts['empty-file']} file(s) are empty (0 bytes) and were skipped.", file=sys.stderr)
    return dict(counts)


# ---------------- Convert PNG to JPEG ----------------

def _has_transparency(img) -> bool:
    """True when an image has at least one pixel that is not fully opaque.
    An alpha channel that is opaque throughout does not count."""
    if img.mode == 'P' and 'transparency' in img.info:
        img = img.convert('RGBA')
    if img.mode not in ('RGBA', 'LA', 'PA'):
        return 'transparency' in img.info
    return img.getchannel('A').getextrema()[0] < 255


def convert_pngs(root: str) -> dict:
    counts = Counter()
    if not HAS_PIL:
        print("Pillow required for PNG conversion; pip install pillow", file=sys.stderr)
        return {}
    for dirpath, dirs, files in os.walk(root):
        _prune_holding(root, dirpath, dirs)
        for name in files:
            if not name.lower().endswith('.png'):
                continue
            if pathlib.Path(name).stem.lower().endswith('-overlay'):
                # Snapchat caption layer: transparent, flattens to a blank image
                counts['skipped-overlay'] += 1
                continue
            p = os.path.join(dirpath, name)
            new = str(pathlib.Path(p).with_suffix('.JPG'))
            if os.path.exists(new):
                counts['already-converted'] += 1
                continue
            img = Image.open(p)
            img.load()
            if _has_transparency(img):
                # JPEG has no transparency; flattening would change the picture
                counts['skipped-transparent'] += 1
                continue
            exif_bytes = img.info.get('exif', b'')
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(new, 'JPEG', quality=95, exif=exif_bytes, optimize=True)
            counts['converted'] += 1
    return dict(counts)


# ---------------- Sync timestamps (safe-only) ----------------

EDITOR_SOFTWARE_HINTS = ('photoshop', 'lightroom', 'camera raw', 'gimp',
                         'affinity', 'luminar', 'pixelmator', 'snapseed',
                         'vsco', 'instagram')


def _is_unedited(meta: dict) -> bool:
    """Heuristic for 'has NOT been manually modified since capture.'
    True when:
      - the EXIF file-level DateTime equals DateTimeOriginal (iOS updates
        DateTime when the user edits a photo), OR DateTime is missing;
      - the Software tag does not match a known editor.
    """
    sw = (meta.get('software') or '').lower()
    for hint in EDITOR_SOFTWARE_HINTS:
        if hint in sw:
            return False
    dt = meta.get('date_taken')
    mt = meta.get('modify_time')
    if dt is None:
        return False
    if mt is None:
        return True
    # Equal within one minute of tolerance (iOS may differ by seconds)
    return abs((mt - dt).total_seconds()) < 60


def _set_creation_time(path: str, ts: float) -> bool:
    """Set the filesystem "Date Created" to the POSIX timestamp ts.
    os.utime only covers accessed/modified, so this goes through the Win32
    SetFileTime API. Returns False on platforms where it isn't supported."""
    if os.name != 'nt':
        return False
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD,
                                wintypes.HANDLE)
    k32.SetFileTime.restype = wintypes.BOOL
    k32.SetFileTime.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
                                ctypes.POINTER(wintypes.FILETIME),
                                ctypes.POINTER(wintypes.FILETIME))
    k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    # FILETIME = 100ns ticks since 1601-01-01 UTC
    ticks = int(round((ts + 11644473600) * 10_000_000))
    ft = wintypes.FILETIME(ticks & 0xFFFFFFFF, ticks >> 32)
    # FILE_WRITE_ATTRIBUTES, share read/write/delete, OPEN_EXISTING
    handle = k32.CreateFileW(os.path.abspath(path), 0x0100, 0x7, None, 3, 0x80, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not k32.SetFileTime(handle, ctypes.byref(ft), None, None):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        k32.CloseHandle(handle)
    return True


def sync_timestamps(root: str) -> dict:
    """Set Date Modified and Date Created to Date Taken on unedited files."""
    counts = Counter()
    for folder, name, full in iter_media(root):
        ftype = detect_type(full) or pathlib.Path(name).suffix.lower()
        meta = read_metadata(full, ftype)
        if meta['date_taken'] is None:
            counts['no-date-taken'] += 1
            continue
        if not _is_unedited(meta):
            counts['skipped-edited'] += 1
            print(f"SKIP (edited): {folder}/{name}")
            continue
        ts = meta['date_taken'].timestamp()
        try:
            os.utime(full, (ts, ts))
            if not _set_creation_time(full, ts):
                counts['created-unsupported'] += 1
            counts['synced'] += 1
            print(f"SYNCED {meta['date_taken']:%Y-%m-%d %H:%M:%S}: {folder}/{name}")
        except Exception as e:
            counts['failed'] += 1
            print(f"FAILED {folder}/{name}: {e}", file=sys.stderr)
    return dict(counts)


# ---------------- Flatten into root ----------------

def flatten(root: str, dry_run: bool = False) -> dict:
    """Move dated files up from their subfolder into root, then remove the
    subfolders that end up empty. Undated files are left in place."""
    counts = Counter()
    verb = 'WOULD MOVE' if dry_run else 'MOVED'
    # Names already claimed in root, lowercased (Windows is case-insensitive)
    taken = {n.lower() for n in os.listdir(root)}
    gone = set()  # paths moved or removed, so a dry run can tell what empties
    for folder, name, full in iter_media(root):
        ftype = detect_type(full) or pathlib.Path(name).suffix.lower()
        dt = read_metadata(full, ftype)['date_taken']
        if dt is None:
            counts['left-undated'] += 1
            print(f"LEFT (no Date Taken): {folder}/{name}")
            continue
        new_name = name
        if new_name.lower() in taken:
            p = pathlib.Path(name)
            new_name = f"{p.stem}_{dt:%Y-%m-%d}{p.suffix}"
            if new_name.lower() in taken:
                counts['collision'] += 1
                print(f"COLLISION, skipping: {folder}/{name}", file=sys.stderr)
                continue
            counts['renamed'] += 1
        if not dry_run:
            try:
                shutil.move(full, os.path.join(root, new_name))
            except OSError as e:
                counts['failed'] += 1
                print(f"FAILED {folder}/{name}: {e}", file=sys.stderr)
                continue
        taken.add(new_name.lower())
        gone.add(full)
        counts['moved'] += 1
        print(f"{verb}: {folder}/{name} -> {new_name}")

    verb = 'WOULD REMOVE EMPTY' if dry_run else 'REMOVED EMPTY'
    holding = tuple(os.path.join(root, d) + os.sep for d in HOLDING_DIRS)
    for dirpath, _dirs, _files in os.walk(root, topdown=False):
        if dirpath == root or (dirpath + os.sep).startswith(holding):
            continue
        if any(os.path.join(dirpath, e) not in gone for e in os.listdir(dirpath)):
            counts['folders-kept'] += 1
            continue
        if not dry_run:
            try:
                os.rmdir(dirpath)
            except OSError as e:
                counts['folders-kept'] += 1
                print(f"FAILED to remove {dirpath}: {e}", file=sys.stderr)
                continue
        gone.add(dirpath)
        counts['folders-removed'] += 1
        print(f"{verb}: {dirpath}")
    return dict(counts)


# ---------------- Quarantine ad images ----------------

# Filename stems that ad images are saved under:
#   0c4cda27-b4cc-4e92-a446-d6b780f24a64   UUID
#   bed51b94a_1595                         9-char hex id (with a letter, so
#                                          20231220_142355 is safe) + number
#   gmsnet2                                gmsnet + optional number
# optionally followed by the _YYYY-MM-DD suffix --flatten adds on a name
# clash, or a " (2)" copy marker.
_AD_NAME_RE = re.compile(
    r'(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    r'|(?=\d*[a-f])[0-9a-f]{9}_\d+'
    r'|gmsnet\d*)'
    r'(?:_\d{4}-\d{2}-\d{2})?(?: \(\d+\))?',
    re.IGNORECASE)


def is_ad_name(name: str) -> bool:
    return _AD_NAME_RE.fullmatch(pathlib.Path(name).stem) is not None


def quarantine_ads(root: str, dry_run: bool = False) -> dict:
    """Move ad images from root and every subfolder into root/_ads, keeping
    their relative path. A file is an ad only if its name matches AND it has
    no camera Make/Model; name matches with camera info are kept and listed.
    Emptied folders are left for --flatten or the cleanup script."""
    counts = Counter()
    if not HAS_PIL:
        # Without Pillow the camera check cannot run, and name alone is not enough
        print("Pillow required to check for camera info; pip install pillow", file=sys.stderr)
        return {}
    verb = 'WOULD QUARANTINE' if dry_run else 'QUARANTINED'
    for dirpath, dirs, files in os.walk(root):
        _prune_holding(root, dirpath, dirs)
        dirs.sort()
        for name in sorted(files):
            if pathlib.Path(name).suffix.lower() not in MEDIA_EXTS or not is_ad_name(name):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            ftype = detect_type(full) or pathlib.Path(name).suffix.lower()
            camera = read_metadata(full, ftype)['camera']
            if camera:
                counts['kept-camera-info'] += 1
                print(f"KEPT (camera: {camera}): {rel}")
                continue
            dst = os.path.join(root, QUARANTINE_DIR, rel)
            if os.path.exists(dst):
                counts['collision'] += 1
                print(f"COLLISION, skipping: {rel}", file=sys.stderr)
                continue
            if not dry_run:
                try:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.move(full, dst)
                except OSError as e:
                    counts['failed'] += 1
                    print(f"FAILED {rel}: {e}", file=sys.stderr)
                    continue
            counts['quarantined'] += 1
            print(f"{verb}: {rel}")
    return dict(counts)


# ---------------- Move files with no image data ----------------

def _has_no_data(path: str) -> bool:
    """True when a file is 0 bytes or contains nothing but null bytes."""
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                return True
            if chunk.count(0) != len(chunk):
                return False


def move_no_data(root: str, dry_run: bool = False) -> dict:
    """Move media files holding no image data from root and every subfolder
    into root/_no-image-data, keeping their relative path (the dated folder
    name may be the only record of when they were taken). Emptied folders are
    left for --flatten or the cleanup script."""
    counts = Counter()
    verb = 'WOULD MOVE' if dry_run else 'MOVED'
    for dirpath, dirs, files in os.walk(root):
        _prune_holding(root, dirpath, dirs)
        dirs.sort()
        for name in sorted(files):
            if pathlib.Path(name).suffix.lower() not in MEDIA_EXTS:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            try:
                if not _has_no_data(full):
                    continue
            except OSError as e:
                counts['failed'] += 1
                print(f"FAILED {rel}: {e}", file=sys.stderr)
                continue
            kind = 'empty' if os.path.getsize(full) == 0 else 'null-filled'
            dst = os.path.join(root, NO_DATA_DIR, rel)
            if os.path.exists(dst):
                counts['collision'] += 1
                print(f"COLLISION, skipping: {rel}", file=sys.stderr)
                continue
            if not dry_run:
                try:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.move(full, dst)
                except OSError as e:
                    counts['failed'] += 1
                    print(f"FAILED {rel}: {e}", file=sys.stderr)
                    continue
            counts['moved-' + kind] += 1
            print(f"{verb} ({kind}): {rel}")
    return dict(counts)


# ---------------- Delete AAE sidecars ----------------

def delete_aae(root: str, dry_run: bool = False) -> dict:
    """Delete every .AAE file (iPhone edit sidecar) in root and every
    subfolder. Emptied folders are left for --flatten or the cleanup script."""
    counts = Counter()
    verb = 'WOULD DELETE' if dry_run else 'DELETED'
    for dirpath, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            if pathlib.Path(name).suffix.lower() != '.aae':
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            if not dry_run:
                try:
                    os.remove(full)
                except OSError as e:
                    counts['failed'] += 1
                    print(f"FAILED {rel}: {e}", file=sys.stderr)
                    continue
            counts['deleted'] += 1
            print(f"{verb}: {rel}")
    return dict(counts)


# ---------------- Reporting ----------------

def write_xlsx(root: str, plan: list, output: str) -> None:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        print("openpyxl not installed; skipping XLSX report. (pip install openpyxl)", file=sys.stderr)
        return
    wb = Workbook()
    header_fill = PatternFill('solid', start_color='305496')
    header_font = Font(name='Arial', bold=True, color='FFFFFF', size=11)
    body_font = Font(name='Arial', size=10)
    thin = Side(border_style='thin', color='BFBFBF')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def style(ws, ncols, widths):
        for c in range(1, ncols + 1):
            cell = ws.cell(row=1, column=c)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='left', vertical='center')
            cell.border = border
        for r in range(2, ws.max_row + 1):
            for c in range(1, ncols + 1):
                cell = ws.cell(row=r, column=c)
                cell.font = body_font
                cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
                cell.border = border
        ws.freeze_panes = 'A2'
        ws.row_dimensions[1].height = 22
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w

    ws = wb.active
    ws.title = 'Summary'
    ws.append(['Metric', 'Value'])
    ws.append(['Files scanned', len(plan)])
    ws.append(['Keep in place', sum(1 for r in plan if r['action'] == 'keep')])
    ws.append(['Move to date-matched folder', sum(1 for r in plan if r['action'] == 'move')])
    ws.append(['Blank Date Taken (would fill)', sum(1 for r in plan if r['action'] == 'fill-blank')])
    style(ws, 2, [44, 10])

    ws2 = wb.create_sheet('Plan')
    cols = ['Current folder', 'Current name', 'Detected type', 'Date Taken',
            'Target folder', 'New name', 'Action']
    ws2.append(cols)
    for r in plan:
        ws2.append([r['current_folder'], r['current_name'], r['detected_type'],
                    r['date_taken'], r['target_folder'], r['new_name'], r['action']])
    style(ws2, len(cols), [14, 32, 10, 22, 14, 32, 24])

    ws3 = wb.create_sheet('Only moves')
    ws3.append(['From folder', 'Current name', 'Date Taken', 'Target folder', 'New name'])
    for r in plan:
        if r['action'] == 'move':
            ws3.append([r['current_folder'], r['current_name'], r['date_taken'],
                        r['target_folder'], r['new_name']])
    style(ws3, 5, [14, 32, 22, 14, 32])

    wb.save(output)


# ---------------- CLI ----------------

# Order phases run in when several are given on one command line: clear out
# junk first, then date, convert, move, sync, and flatten last (once files are
# in the root the other phases no longer see them).
PHASE_ORDER = ('delete_aae', 'move_no_data', 'quarantine_ads', 'fill_blanks', 'convert_png',
               'apply_moves', 'sync_timestamps', 'flatten')
ALL_PHASES = ('delete_aae', 'fill_blanks', 'convert_png', 'apply_moves', 'sync_timestamps')
DRY_RUN_PHASES = ('flatten', 'quarantine_ads', 'move_no_data', 'delete_aae')

# Most problem lines repeated per phase in the closing summary
MAX_SUMMARY_ISSUES = 50


class _IssueTee:
    """Pass stderr through unchanged while keeping a copy of each line, so
    the problems a phase reported can be repeated in the closing summary."""

    def __init__(self, stream):
        self.stream = stream
        self.text = ''

    def write(self, s):
        self.text += s
        return self.stream.write(s)

    def flush(self):
        self.stream.flush()

    def lines(self) -> list:
        return [ln for ln in self.text.splitlines() if ln.strip()]


def _run_phase(phase: str, args) -> dict:
    if phase == 'delete_aae':
        return delete_aae(args.root, args.dry_run)
    if phase == 'move_no_data':
        return move_no_data(args.root, args.dry_run)
    if phase == 'quarantine_ads':
        return quarantine_ads(args.root, args.dry_run)
    if phase == 'fill_blanks':
        return fill_blanks(args.root)
    if phase == 'convert_png':
        return convert_pngs(args.root)
    if phase == 'sync_timestamps':
        return sync_timestamps(args.root)
    if phase == 'flatten':
        return flatten(args.root, args.dry_run)
    # report-only and apply-moves both need the scanned plan
    plan = scan(args.root)
    out_xlsx = os.path.join(args.root, args.xlsx)
    write_xlsx(args.root, plan, out_xlsx)
    print(f"Audit workbook: {out_xlsx}")
    if phase == 'apply_moves':
        return apply_moves(args.root, plan)
    return dict(Counter(r['action'] for r in plan))


def _print_summary(results: list) -> None:
    """Print every phase's counts and reported problems together, so a run of
    several phases can be read from the end of the output."""
    print()
    print('=' * 24 + ' Summary of this run ' + '=' * 24)
    for key, counts, issues in results:
        print(f"\n{key}")
        if not counts:
            print("    nothing to do")
        width = max((len(k) for k in counts), default=0)
        for k, v in counts.items():
            print(f"    {k:<{width}}  {v:>7}")
        if issues:
            print(f"    problems reported: {len(issues)}")
            for ln in issues[:MAX_SUMMARY_ISSUES]:
                print(f"      {ln}")
            if len(issues) > MAX_SUMMARY_ISSUES:
                print(f"      ... and {len(issues) - MAX_SUMMARY_ISSUES} more (see above)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', required=True, help='Photo folder root (e.g. D:\\Pictures\\2026)')
    ap.add_argument('--report-only', action='store_true', help='Scan and write audit XLSX; no changes. Cannot be combined with other phases.')
    ap.add_argument('--all', action='store_true', help='Run --delete-aae, --fill-blanks, --convert-png, --apply-moves and --sync-timestamps in that order, then print one summary of all of them.')
    ap.add_argument('--fill-blanks', action='store_true', help='Write Date Taken into EXIF for files whose Date Taken is blank, using the date in the filename, else the folder date.')
    ap.add_argument('--convert-png', action='store_true', help='Convert PNG files to JPEG (preserving EXIF).')
    ap.add_argument('--apply-moves', action='store_true', help='Move files whose Date Taken differs from the folder name.')
    ap.add_argument('--sync-timestamps', action='store_true', help='Set Date Modified/Created to Date Taken for files that have not been edited.')
    ap.add_argument('--flatten', action='store_true', help='Move files that have a Date Taken up out of their subfolders into the root, then delete the emptied subfolders.')
    ap.add_argument('--quarantine-ads', action='store_true', help='Move ad images (ad-style filename AND no camera Make/Model) from the root and every subfolder into an _ads folder for review. Nothing is deleted.')
    ap.add_argument('--move-no-data', action='store_true', help='Move media files that hold no image data (0 bytes or all null bytes) from the root and every subfolder into a _no-image-data folder. Nothing is deleted.')
    ap.add_argument('--delete-aae', action='store_true', help='Permanently delete every .AAE file (iPhone edit sidecar) in the root and every subfolder.')
    ap.add_argument('--dry-run', action='store_true', help='With --flatten, --quarantine-ads, --move-no-data or --delete-aae: list what would be moved, removed or deleted without changing anything.')
    ap.add_argument('--xlsx', default='photo-audit.xlsx', help='Audit workbook filename (relative to root).')
    args = ap.parse_args(argv)

    phases = [p for p in PHASE_ORDER
              if getattr(args, p) or (args.all and p in ALL_PHASES)]
    if args.report_only:
        if phases:
            ap.error('--report-only cannot be combined with other phases')
        phases = ['report_only']
    if not phases:
        ap.error('choose at least one phase (e.g. --report-only, --fill-blanks, --all)')
    if args.dry_run and any(p not in DRY_RUN_PHASES for p in phases):
        ap.error('--dry-run is only supported with --flatten, --quarantine-ads, --move-no-data and --delete-aae')

    if not os.path.isdir(args.root):
        print(f"Not a directory: {args.root}", file=sys.stderr)
        return 2

    results = []
    for phase in phases:
        key = phase + '_dry_run' if args.dry_run else phase
        if len(phases) > 1:
            print(f"\n----- {key} -----")
        tee = _IssueTee(sys.stderr)
        sys.stderr = tee
        try:
            counts = _run_phase(phase, args)
        finally:
            sys.stderr = tee.stream
        print(json.dumps({key: counts}, indent=2))
        results.append((key, counts, tee.lines()))
    if len(phases) > 1:
        _print_summary(results)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
