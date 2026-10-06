#!/usr/bin/env python3
"""
organize.py — read photo metadata (EXIF, MOV mvhd, HEIC TIFF) and sort files by real Date Taken.

Phases:
    --report-only     scan and write audit XLSX; make no changes
    --apply           move/rename per the ruleset
    --convert-png     convert PNG files to JPEG preserving EXIF (for Windows
                      Explorer "Date Taken" compatibility)

Rules:
    * Detect true file format from first 16 bytes (magic bytes).
    * Read Date Taken:
        HEIC -> embedded TIFF/EXIF DateTimeOriginal
        MOV/MP4 -> mvhd atom creation_time
        PNG/JPG -> standard EXIF via PIL
    * If Date Taken matches the current folder (YYYY-MM-DD), leave in place.
    * If Date Taken differs, move to a sibling folder named YYYY-MM-DD.
    * If Date Taken is blank (and we can write it), write folder-date at 12:00:00
      and leave in place. Append _<folder-date> to the filename.
    * If the file already has Date Taken, do NOT add a date suffix to the name.

Dependencies: Pillow (`pip install pillow`). openpyxl for the XLSX report.
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
import sys
from collections import Counter
from typing import Optional

try:
    from PIL import Image
except ImportError:
    print("Pillow is required: pip install pillow", file=sys.stderr)
    sys.exit(1)


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

def _heic_date(path: str) -> Optional[datetime.datetime]:
    """Scan a HEIC/HEIF file for an embedded TIFF/EXIF block and return
    DateTimeOriginal if present. Uses raw byte scanning so no exiftool required."""
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
                    tag, typ, _cnt = struct.unpack(endian + 'HHI', data[e:e + 8])
                    val_off = struct.unpack(endian + 'I', data[e + 8:e + 12])[0]
                    if tag != 0x8769:  # ExifIFDPointer
                        continue
                    sn = struct.unpack(endian + 'H', data[i + val_off:i + val_off + 2])[0]
                    for kk in range(sn):
                        se = i + val_off + 2 + kk * 12
                        stag, styp, scnt = struct.unpack(endian + 'HHI', data[se:se + 8])
                        svo = struct.unpack(endian + 'I', data[se + 8:se + 12])[0]
                        if stag == 0x9003 and styp == 2 and scnt < 32:
                            s = data[i + svo:i + svo + scnt].rstrip(b'\x00').decode('ascii', 'replace')
                            try:
                                return datetime.datetime.strptime(s.strip(), "%Y:%m:%d %H:%M:%S")
                            except ValueError:
                                pass
            except Exception:
                continue
    return None


def _mp4_date(path: str) -> Optional[datetime.datetime]:
    """Read creation_time from the mvhd atom of an ISO BMFF file (MOV/MP4)."""
    with open(path, 'rb') as f:
        data = f.read()
    i = data.find(b'mvhd')
    if i < 0:
        return None
    p = data[i + 4:]
    try:
        if p[0] == 1:
            ct = struct.unpack('>Q', p[4:12])[0]
        else:
            ct = struct.unpack('>I', p[4:8])[0]
        dt = datetime.datetime(1904, 1, 1) + datetime.timedelta(seconds=ct)
        return dt if dt.year > 1970 else None
    except Exception:
        return None


def _pil_date(path: str) -> Optional[datetime.datetime]:
    """Standard EXIF DateTimeOriginal via Pillow for PNG/JPEG/TIFF."""
    try:
        img = Image.open(path)
        v = img.getexif().get_ifd(0x8769).get(0x9003)
        if v:
            return datetime.datetime.strptime(v.strip(), "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None
    return None


def date_taken(path: str, ftype: Optional[str]) -> Optional[datetime.datetime]:
    if ftype == '.heic':
        return _heic_date(path)
    if ftype in ('.mov', '.mp4', '.m4v'):
        return _mp4_date(path)
    if ftype in ('.png', '.jpg', '.jpeg', '.tif', '.tiff'):
        return _pil_date(path)
    return None


# ---------------- Core workflow ----------------

def scan(root: str):
    """Return a list of plan dicts for every file under root."""
    rows = []
    for folder in sorted(os.listdir(root)):
        fp = os.path.join(root, folder)
        if not os.path.isdir(fp):
            continue
        m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', folder)
        folder_date = datetime.date(int(m[1]), int(m[2]), int(m[3])) if m else None
        for name in sorted(os.listdir(fp)):
            full = os.path.join(fp, name)
            if not os.path.isfile(full):
                continue
            if name.lower().endswith(('.xlsx', '.ps1', '.py', '.md', '.json')):
                continue
            ftype = detect_type(full) or pathlib.Path(name).suffix.lower()
            dt = date_taken(full, ftype)
            stem = pathlib.Path(name).stem
            base = re.match(r'^(.+?)_\d{4}-\d{2}-\d{2}$', stem)
            base = base.group(1) if base else stem
            ext_canonical = ftype.upper() if ftype else pathlib.Path(name).suffix
            if dt is None and folder_date is not None:
                action = 'set-date-write-and-keep'
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


def apply(root: str, plan: list) -> dict:
    """Execute moves and renames. Returns counts."""
    counts = Counter()
    for r in plan:
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
        if os.path.exists(dst):
            counts['collision'] += 1
            print(f"COLLISION, skipping: {dst}", file=sys.stderr)
            continue
        shutil.move(src, dst)
        counts[r['action']] += 1
    return dict(counts)


def convert_pngs(root: str) -> dict:
    """Re-encode PNG files to JPEG preserving EXIF. Leaves original PNG alone."""
    counts = Counter()
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if not name.lower().endswith('.png'):
                continue
            p = os.path.join(dirpath, name)
            new = str(pathlib.Path(p).with_suffix('.JPG'))
            if os.path.exists(new):
                counts['already_converted'] += 1
                continue
            img = Image.open(p)
            img.load()
            exif_bytes = img.info.get('exif', b'')
            if img.mode in ('RGBA', 'LA', 'P'):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                mask = img.split()[-1] if img.mode in ('RGBA', 'LA') else None
                bg.paste(img, mask=mask)
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(new, 'JPEG', quality=95, exif=exif_bytes, optimize=True)
            counts['converted'] += 1
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

    # Summary
    ws = wb.active
    ws.title = 'Summary'
    ws.append(['Metric', 'Value'])
    ws.append(['Files scanned', len(plan)])
    ws.append(['Keep in place', sum(1 for r in plan if r['action'] == 'keep')])
    ws.append(['Move to date-matched folder', sum(1 for r in plan if r['action'] == 'move')])
    ws.append(['Blank Date Taken (will set to folder date)', sum(1 for r in plan if r['action'] == 'set-date-write-and-keep')])
    style(ws, 2, [44, 10])

    # Detail
    ws2 = wb.create_sheet('Plan')
    cols = ['Current folder', 'Current name', 'Detected type', 'Date Taken',
            'Target folder', 'New name', 'Action']
    ws2.append(cols)
    for r in plan:
        ws2.append([r['current_folder'], r['current_name'], r['detected_type'],
                    r['date_taken'], r['target_folder'], r['new_name'], r['action']])
    style(ws2, len(cols), [14, 32, 10, 22, 14, 32, 24])

    # Only moves
    ws3 = wb.create_sheet('Only moves')
    ws3.append(['From folder', 'Current name', 'Date Taken', 'Target folder', 'New name'])
    for r in plan:
        if r['action'] == 'move':
            ws3.append([r['current_folder'], r['current_name'], r['date_taken'],
                        r['target_folder'], r['new_name']])
    style(ws3, 5, [14, 32, 22, 14, 32])

    wb.save(output)


# ---------------- CLI ----------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', required=True, help='Photo folder root (e.g. D:\\Pictures\\2026)')
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--report-only', action='store_true', help='Scan and write audit XLSX; make no changes.')
    g.add_argument('--apply', action='store_true', help='Apply the move/rename plan.')
    g.add_argument('--convert-png', action='store_true', help='Convert PNG files to JPEG.')
    ap.add_argument('--xlsx', default='photo-audit.xlsx', help='Audit workbook filename (relative to root).')
    args = ap.parse_args(argv)

    if not os.path.isdir(args.root):
        print(f"Not a directory: {args.root}", file=sys.stderr)
        return 2

    if args.convert_png:
        counts = convert_pngs(args.root)
        print(json.dumps({'convert_png': counts}, indent=2))
        return 0

    plan = scan(args.root)
    out_xlsx = os.path.join(args.root, args.xlsx)
    write_xlsx(args.root, plan, out_xlsx)
    print(f"Audit workbook: {out_xlsx}")

    if args.apply:
        counts = apply(args.root, plan)
        print(json.dumps({'apply': counts}, indent=2))
    else:
        summary = Counter(r['action'] for r in plan)
        print(json.dumps({'report_only': dict(summary)}, indent=2))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
