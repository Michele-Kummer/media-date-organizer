"""Smoke tests for organize.py: each builds a small photo folder in a temp
directory, runs the real command line, and checks the main outcome.

Run from the repository root:
    py -m unittest discover tests -v
"""
import contextlib
import datetime
import io
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]
                       / 'skills' / 'media-date-organizer' / 'scripts'))
import organize  # noqa: E402


def make_image(path, color=(200, 30, 30), taken=None, fmt=None):
    """Write a small picture with a pattern (so shrinking keeps it
    recognisable), optionally with a Date Taken."""
    img = Image.new('RGB', (64, 48), color)
    for x in range(0, 64, 8):
        img.putpixel((x, x % 48), (255, 255, 255))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, fmt)
    if taken is not None:
        organize._write_exif_date_image(str(path), taken)


def date_taken(path):
    return organize.read_metadata(str(path), organize.detect_type(str(path)))['date_taken']


def run(root, *flags):
    """Run organize.py's command line on root; return (exit code, output)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = organize.main(['--root', str(root), *flags])
    return code, out.getvalue()


def names(folder):
    """Lowercased file names in folder (Windows ignores case)."""
    return sorted(n.lower() for n in os.listdir(folder)) if os.path.isdir(folder) else []


class SmokeTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_report_only_plans_a_move_and_changes_nothing(self):
        make_image(self.root / '2020-01-01' / 'right.jpg', taken=datetime.datetime(2020, 1, 1, 10, 0, 0))
        make_image(self.root / '2020-01-01' / 'wrong.jpg', taken=datetime.datetime(2020, 2, 2, 9, 30, 0))

        code, _ = run(self.root, '--report-only')

        self.assertEqual(code, 0)
        plan = {r['current_name']: r for r in organize.scan(str(self.root))}
        self.assertEqual(plan['right.jpg']['action'], 'keep')
        self.assertEqual(plan['wrong.jpg']['action'], 'move')
        self.assertEqual(plan['wrong.jpg']['target_folder'], '2020-02-02')
        self.assertEqual(names(self.root / '2020-01-01'), ['right.jpg', 'wrong.jpg'])
        self.assertFalse((self.root / '2020-02-02').exists())
        self.assertTrue(any(n.startswith('media_audit_') and n.endswith('.xlsx') for n in names(self.root)))

    def test_all_cleans_dates_converts_and_moves(self):
        day = self.root / '2020-01-01'
        make_image(day / 'wrong.jpg', taken=datetime.datetime(2020, 2, 2, 9, 30, 0))
        make_image(day / 'IMG_20210304_101112.jpg')           # no Date Taken, date in the name
        make_image(day / 'shot.png', taken=datetime.datetime(2020, 1, 1, 8, 0, 0))
        (day / 'empty.jpg').write_bytes(b'')                   # a failed copy
        (day / 'IMG_0001.AAE').write_text('edit sidecar')
        (day / 'Thumbs.db').write_bytes(b'cache')

        code, _ = run(self.root, '--all')

        self.assertEqual(code, 0)
        # Junk deleted, the incomplete file set aside
        self.assertNotIn('img_0001.aae', names(day))
        self.assertNotIn('thumbs.db', names(day))
        self.assertEqual(names(self.root / '_incomplete' / '2020-01-01'), ['empty.jpg'])
        # Blank date filled from the filename, then both strays moved to their real day
        self.assertEqual(names(self.root / '2020-02-02'), ['wrong.jpg'])
        filled = self.root / '2021-03-04' / 'IMG_20210304_101112.jpg'
        self.assertTrue(filled.exists())
        self.assertEqual(date_taken(filled), datetime.datetime(2021, 3, 4, 10, 11, 12))
        # PNG converted, original left for the cleanup script, date carried over
        self.assertIn('shot.png', names(day))
        self.assertIn('shot.jpg', names(day))
        self.assertEqual(date_taken(day / 'shot.jpg'), datetime.datetime(2020, 1, 1, 8, 0, 0))

    def test_quarantine_ads_moves_only_ad_names(self):
        day = self.root / '2020-01-01'
        ads = ['0c4cda27-b4cc-4e92-a446-d6b780f24a64.jpg',
               '54ac2fda0a6755305200011c-b30-600.jpg',
               '55d58970f6cd4574f635d6e3_568-1443241239.jpg']
        for name in ads:
            make_image(day / name)
        make_image(day / 'IMG_20200101_120000.jpg')

        code, out = run(self.root, '--quarantine-ads', '--dry-run')
        self.assertEqual(code, 0)
        self.assertEqual(len(names(day)), 4, 'a dry run must not move anything')
        self.assertIn('WOULD', out)

        code, _ = run(self.root, '--quarantine-ads')
        self.assertEqual(code, 0)
        self.assertEqual(names(day), ['img_20200101_120000.jpg'])
        self.assertEqual(names(self.root / '_ads' / '2020-01-01'), sorted(ads))

    def test_flatten_moves_dated_files_up_and_keeps_undated(self):
        make_image(self.root / '2020-01-01' / 'a.jpg', taken=datetime.datetime(2020, 1, 1, 10, 0, 0))
        make_image(self.root / '2020-01-02' / 'a.jpg', color=(0, 0, 200),
                   taken=datetime.datetime(2020, 1, 2, 10, 0, 0))
        make_image(self.root / 'misc' / 'undated.jpg')

        code, _ = run(self.root, '--flatten')

        self.assertEqual(code, 0)
        # Same name from two days: the second gets its date as a suffix
        self.assertIn('a.jpg', names(self.root))
        self.assertIn('a_2020-01-02.jpg', names(self.root))
        self.assertFalse((self.root / '2020-01-01').exists())
        self.assertFalse((self.root / '2020-01-02').exists())
        self.assertEqual(names(self.root / 'misc'), ['undated.jpg'])

    def test_duplicate_checks_tell_copies_from_different_pictures(self):
        day = self.root / '2020-01-01'
        make_image(day / 'same.png')
        make_image(day / 'same.jpg')                              # same picture, other format
        make_image(day / 'other.png', color=(200, 30, 30))
        make_image(day / 'other.jpg', color=(20, 160, 60))        # same name, different picture
        # A name clash --flatten resolved with a date suffix: a true copy
        make_image(self.root / 'clip.jpg', taken=datetime.datetime(2020, 1, 1, 10, 0, 0))
        shutil.copyfile(self.root / 'clip.jpg', self.root / 'clip_2020-01-01.jpg')
        before = sorted(str(p) for p in self.root.rglob('*') if p.suffix != '.xlsx')

        code, out = run(self.root, '--compare-collisions')
        self.assertEqual(code, 0)
        self.assertIn('IDENTICAL', out)
        self.assertIn('clip_2020-01-01.jpg | clip.jpg', out)

        code, out = run(self.root, '--visual-compare', '--dry-run')
        self.assertEqual(code, 0)
        verdicts = {ln.split(': ', 1)[1].split(' - ')[0]: ln.split(':')[0]
                    for ln in out.splitlines() if ' | ' in ln}
        self.assertEqual(verdicts['clip_2020-01-01.jpg | clip.jpg'], 'IDENTICAL (confidence certain, byte for byte)')
        self.assertEqual(verdicts[os.path.join('2020-01-01', 'same.png') + ' | ' + os.path.join('2020-01-01', 'same.jpg')],
                         'DUPLICATE (confidence high)')
        self.assertEqual(verdicts[os.path.join('2020-01-01', 'other.png') + ' | ' + os.path.join('2020-01-01', 'other.jpg')],
                         'DIFFERENT (confidence high)')
        # Report only: no file added, removed or renamed
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob('*') if p.suffix != '.xlsx'))
        # And it refuses to run as anything but a dry run
        with self.assertRaises(SystemExit):
            run(self.root, '--visual-compare')


if __name__ == '__main__':
    unittest.main()
