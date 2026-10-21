#!/usr/bin/env python3
"""
find_duplicates.py — report photos and videos that are the same file saved
twice, or are likely the same picture or recording. No photo or video is
moved, renamed or deleted; the report is the whole job.

    py find_duplicates.py --root "D:\\Pictures\\2012"
    py find_duplicates.py --root "D:\\Pictures"

Every photo and video under --root is looked at, at any depth (the _ads and
_incomplete holding folders are left out). The report has three kinds of
line, surest first:

    IDENTICAL (confidence certain, byte for byte): <copy> | <first>
        The two files hold exactly the same bytes. Found by size, then by
        hashing the files that share a size.
    DUPLICATE (confidence high|medium): <file> | <file> - <why>
        Different bytes, but the pictures look the same: a re-saved, resized
        or re-tagged copy.
    POSSIBLE (confidence low): <file> | <file> - <why>
        Worth a look: the pictures are close but not clearly the same, or
        they could not be compared.

Only files with something in common are compared by their pixels, since
comparing every file with every other would take hours. Two files of the
same kind (two photos, or two videos) are compared when they share any of:

    - the same Date Taken (photos) or Media Created (videos), to the second;
    - the same name, ignoring the extension and copy endings such as
      " (1)", " - Copy" and the _YYYY-MM-DD ending --flatten adds;
    - the same size in bytes.

Pairs that turn out to be different pictures (burst shots taken in the same
second, two cameras that both used IMG_0001) are counted, not listed. Videos
are compared by four frames and their length, which needs ffmpeg
(pip install "imageio-ffmpeg>=0.5"); without it, matching videos are listed as
POSSIBLE.

The run is appended to the Run log and Run counts sheets of the audit
workbook in --root, the same workbook organize.py records its runs in.
"""
from __future__ import annotations

import argparse
import datetime
import functools
import hashlib
import itertools
import json
import os
import pathlib
import re
import sys
from collections import Counter, defaultdict

# organize.py reads the dates, compares the pictures and keeps the audit workbook
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'media-date-organizer' / 'scripts'))
import organize  # noqa: E402

VIDEO_KIND_EXTS = organize.VIDEO_EXTS + organize.CAMCORDER_EXTS
ALL_EXTS = organize.MEDIA_EXTS | set(organize.CAMCORDER_EXTS)

# Bytes hashed first, to tell most same-sized files apart without reading them whole
HEAD_BYTES = 64 * 1024

# Endings a copy of a file is given: " (1)", " - Copy", and --flatten's _YYYY-MM-DD
_COPY_ENDING_RE = re.compile(r'(?:\s*\(\d+\)|\s*-\s*copy|_\d{4}-\d{2}-\d{2})$', re.IGNORECASE)


def _iter_files(root: str):
    """Yield the full path of every photo and video under root, at any depth,
    leaving out the holding folders."""
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in organize.HOLDING_DIRS)
        for name in sorted(files):
            if pathlib.Path(name).suffix.lower() in ALL_EXTS:
                yield os.path.join(dirpath, name)


def _digest(path: str, limit: int = None) -> bytes:
    """Return the SHA-256 of a file, or of its first limit bytes."""
    h = hashlib.sha256()
    left = limit
    with open(path, 'rb') as f:
        while left is None or left > 0:
            chunk = f.read(1024 * 1024 if left is None else min(left, 1024 * 1024))
            if not chunk:
                break
            h.update(chunk)
            if left is not None:
                left -= len(chunk)
    return h.digest()


def _identical_groups(by_size: dict, counts: Counter) -> list:
    """Return lists of byte-identical files, each sorted, from files grouped
    by size. Files that cannot be read are counted and left out."""
    groups = []
    for paths in by_size.values():
        if len(paths) < 2:
            continue
        for whole in (False, True):
            by_hash = defaultdict(list)
            for p in paths:
                try:
                    by_hash[_digest(p, None if whole else HEAD_BYTES)].append(p)
                except OSError as e:
                    counts['read-failed'] += 1
                    print(f"FAILED to read {p}: {e}", file=sys.stderr)
            if not whole:
                # Only files whose first bytes match are worth reading whole
                paths = [p for same in by_hash.values() if len(same) > 1 for p in same]
        groups += [sorted(same, key=_path_order) for same in by_hash.values() if len(same) > 1]
    return groups


def _path_order(path: str) -> tuple:
    """Sort key that puts the file nearest the root first, then by name."""
    return path.count(os.sep), path.lower()


def _name_key(path: str) -> str:
    """Return a file's name without its extension or any copy endings,
    lowercased."""
    stem = pathlib.Path(path).stem.lower()
    while True:
        shorter = _COPY_ENDING_RE.sub('', stem)
        if shorter == stem or not shorter:
            return stem
        stem = shorter


_ffmpeg = functools.lru_cache(maxsize=None)(organize._find_ffmpeg)


@functools.lru_cache(maxsize=512)
def _signature(path: str, kind: str) -> tuple:
    """Return ((video length or None, width, height, small pictures), None)
    to compare a file by, or (None, why it could not be read). A photo gives
    one picture, a video one for each of organize.VISUAL_FRAME_POSITIONS."""
    edge = organize.VISUAL_COMPARE_EDGE
    try:
        if not organize.HAS_PIL:
            raise ValueError('Pillow is needed to compare pictures (pip install "pillow>=10.0")')
        if kind == 'video':
            if _ffmpeg() is None:
                raise ValueError('ffmpeg is needed to compare videos (pip install "imageio-ffmpeg>=0.5")')
            length, frames = organize._video_frames(_ffmpeg(), path)
            width, height = frames[0].size
        else:
            length = None
            with organize.Image.open(path) as img:
                width, height = img.size
                img.draft('RGB', (edge * 2, edge * 2))  # JPEG: decode small, much faster
                frames = [img.convert('RGB')]
        return (length, width, height, tuple(f.convert('RGB').resize((edge, edge)) for f in frames)), None
    except Exception as e:
        return None, str(e) or type(e).__name__


def _judge(a: tuple, b: tuple) -> tuple:
    """Return (verdict, confidence, reason) for whether two signatures show
    the same picture or recording, by the rules of organize._visual_verdict."""
    tolerance = organize.VISUAL_SHAPE_TOLERANCE
    (a_len, a_w, a_h, a_pics), (b_len, b_w, b_h, b_pics) = a, b
    if a_len is not None and abs(a_len - b_len) > max(0.2, tolerance * max(a_len, b_len)):
        return 'different', 'high', f"video lengths differ, {a_len:.1f}s vs {b_len:.1f}s"
    if abs(a_w / a_h - b_w / b_h) > tolerance * (a_w / a_h):
        return 'different', 'high', f"shapes differ, {a_w}x{a_h} vs {b_w}x{b_h}"
    # Judge a video by its least alike pair of frames
    worst = max(organize._pixel_difference(x, y) for x, y in zip(a_pics, b_pics))
    what = f"pixel difference {worst:.1f}%"
    if a_len is not None:
        what += f" at the least alike of {len(a_pics)} frames, both {a_len:.1f}s long"
    if (a_w, a_h) != (b_w, b_h):
        what += f", sizes {a_w}x{a_h} vs {b_w}x{b_h}"
    for limit, verdict, confidence in organize.VISUAL_VERDICTS:
        if worst <= limit:
            return verdict, confidence, what
    return 'different', 'high', what


def find_duplicates(root: str) -> dict:
    """Print every pair of identical or likely duplicate files under root
    and return the counts. Changes nothing."""
    counts = Counter()

    def rel(path):
        return os.path.relpath(path, root).replace(os.sep, '/')

    by_size = defaultdict(list)
    for full in _iter_files(root):
        try:
            size = os.path.getsize(full)
        except OSError as e:
            counts['read-failed'] += 1
            print(f"FAILED to read {rel(full)}: {e}", file=sys.stderr)
            continue
        if size == 0:
            # A failed copy or transfer: every empty file would match every other
            counts['empty-file'] += 1
            continue
        counts['files-checked'] += 1
        by_size[size].append(full)
    sizes = {p: size for size, paths in by_size.items() for p in paths}

    # Byte-identical copies. Each group is stood for by its first file from here on
    first_of = {}
    for group in _identical_groups(by_size, counts):
        counts['identical-groups'] += 1
        for copy in group[1:]:
            first_of[copy] = group[0]
            counts['identical-copies'] += 1
            counts['identical-copies-bytes'] += sizes[copy]
            print(f"IDENTICAL (confidence certain, byte for byte): {rel(copy)} | {rel(group[0])}")

    # What each remaining file has in common with others of its kind
    kinds, dates = {}, {}
    alike = defaultdict(list)
    for full in sorted((p for p in sizes if p not in first_of), key=_path_order):
        ftype = organize.detect_type(full) or pathlib.Path(full).suffix.lower()
        kind = kinds[full] = 'video' if ftype in VIDEO_KIND_EXTS else 'photo'
        try:
            dates[full] = organize.read_metadata(full, ftype)['date_taken']
        except (OSError, MemoryError):
            dates[full] = None
        if dates[full] is not None:
            alike[('date', kind, dates[full])].append(full)
        alike[('name', kind, _name_key(full))].append(full)
        alike[('size', kind, sizes[full])].append(full)
    pairs = defaultdict(set)
    for (shared, _kind, _value), paths in alike.items():
        for pair in itertools.combinations(paths, 2):
            pairs[pair].add(shared)

    found = []
    for (b, a), shared in pairs.items():
        kind = kinds[a]
        why = []
        if 'date' in shared:
            why.append(f"same {'Media Created' if kind == 'video' else 'Date Taken'} {dates[a]:%Y-%m-%d %H:%M:%S}")
        if 'name' in shared:
            why.append('same name')
        if 'size' in shared:
            why.append(f"same size {sizes[a]:,} bytes")
        sig_a, err_a = _signature(a, kind)
        sig_b, err_b = _signature(b, kind)
        if sig_a is None or sig_b is None:
            counts['possible-not-compared'] += 1
            found.append((2, f"POSSIBLE (confidence low): {rel(a)} | {rel(b)} - {', '.join(why)}; "
                             f"not compared: {err_a or err_b}"))
            continue
        verdict, confidence, reason = _judge(sig_a, sig_b)
        if verdict == 'different':
            counts['alike-but-different'] += 1
            continue
        word, order = ('DUPLICATE', 1) if verdict == 'duplicate' else ('POSSIBLE', 2)
        counts[f"{word.lower()}-{confidence}"] += 1
        found.append((order if confidence != 'high' else 0,
                      f"{word} (confidence {confidence}): {rel(a)} | {rel(b)} - {', '.join(why)}; {reason}"))
    for _order, line in sorted(found):
        print(line)

    likely = sum(v for k, v in counts.items() if k.startswith('duplicate-'))
    possible = sum(v for k, v in counts.items() if k.startswith('possible-'))
    print(f"DUPLICATES: {counts['files-checked']:,} file(s) checked; "
          f"{counts['identical-copies']:,} identical copy(ies) in {counts['identical-groups']:,} group(s) "
          f"({counts['identical-copies-bytes'] / 1024 / 1024:,.1f} MB), "
          f"{likely:,} likely duplicate pair(s), {possible:,} possible pair(s)")
    return dict(counts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', required=True, help='Folder to search, at any depth: one year (D:\\Pictures\\2012) or the folder holding the year folders (D:\\Pictures).')
    ap.add_argument('--xlsx', help='Audit workbook filename (relative to root). Defaults to the workbook organize.py uses, <root folder name>_<photos|videos>_media_audit_<today>.xlsx.')
    args = ap.parse_args(argv)
    if not os.path.isdir(args.root):
        print(f"Not a directory: {args.root}", file=sys.stderr)
        return 2
    started = datetime.datetime.now()
    out_xlsx = os.path.join(args.root, args.xlsx or organize._default_xlsx(args.root))

    log = []
    tee = organize._IssueTee(sys.stderr, log)
    out = organize._IssueTee(sys.stdout, log)
    sys.stderr, sys.stdout = tee, out
    try:
        counts = find_duplicates(args.root)
    finally:
        sys.stderr, sys.stdout = tee.stream, out.stream
    print(json.dumps({'find_duplicates': counts}, indent=2))
    organize.append_audit_log(out_xlsx, started, [('find_duplicates', False, counts, log)])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
