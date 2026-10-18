"""Smoke test for find_duplicates.py: builds a small photo folder in a temp
directory, runs the real command line, and checks what it reports.

Run from the repository root:
    py -m unittest discover tests -v
"""
import contextlib
import datetime
import io
import pathlib
import shutil
import sys
import tempfile
import unittest

from PIL import Image

from test_smoke import make_image, organize

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]
                       / 'skills' / 'find-duplicates' / 'scripts'))
import find_duplicates  # noqa: E402


def run(root):
    """Run find_duplicates.py's command line on root; return (exit code, output)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = find_duplicates.main(['--root', str(root)])
    return code, out.getvalue()


class FindDuplicatesTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='find-duplicates-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_reports_identical_and_likely_duplicates_and_changes_nothing(self):
        taken = datetime.datetime(2020, 1, 1, 10, 0, 0)
        # The same file in two folders, three levels apart
        make_image(self.root / 'a.jpg', taken=taken)
        (self.root / 'Trip' / 'Day 1').mkdir(parents=True)
        shutil.copyfile(self.root / 'a.jpg', self.root / 'Trip' / 'Day 1' / 'copy of a.jpg')
        # The same picture saved again: other bytes, other name, same Date Taken
        with Image.open(self.root / 'a.jpg') as img:
            img.save(self.root / 'Trip' / 'resaved.jpg', quality=40)
        organize._write_exif_date_image(str(self.root / 'Trip' / 'resaved.jpg'), taken)
        # A smaller copy with no date, named the way Windows names a copy
        make_image(self.root / 'Trip' / 'b.jpg', color=(20, 160, 60))
        with Image.open(self.root / 'Trip' / 'b.jpg') as img:
            img.resize((32, 24)).save(self.root / 'Trip' / 'b (1).jpg')
        # Alike but different: a burst shot in the same second, and a reused name
        make_image(self.root / 'burst.jpg', color=(0, 0, 200), taken=taken)
        make_image(self.root / '2020-01-01' / 'b.jpg', color=(250, 250, 0))
        # Holding folders are left out
        (self.root / '_ads').mkdir()
        shutil.copyfile(self.root / 'a.jpg', self.root / '_ads' / 'a.jpg')
        before = sorted(str(p) for p in self.root.rglob('*'))

        code, out = run(self.root)

        self.assertEqual(code, 0)
        self.assertIn('IDENTICAL (confidence certain, byte for byte): Trip/Day 1/copy of a.jpg | a.jpg', out)
        self.assertIn('DUPLICATE (confidence high): Trip/resaved.jpg | a.jpg - same Date Taken 2020-01-01 10:00:00;', out)
        self.assertIn('DUPLICATE (confidence high): Trip/b.jpg | Trip/b (1).jpg - same name;', out)
        self.assertIn('sizes 64x48 vs 32x24', out)
        self.assertNotIn('burst.jpg', out)
        self.assertNotIn('2020-01-01/b.jpg', out)
        self.assertNotIn('_ads', out)
        self.assertIn('"identical-copies": 1', out)
        self.assertIn('"duplicate-high": 2', out)
        self.assertIn('1 identical copy(ies) in 1 group(s)', out)
        after = sorted(str(p) for p in self.root.rglob('*') if p.suffix != '.xlsx')
        self.assertEqual(after, before, 'a report must not change anything')


if __name__ == '__main__':
    unittest.main()
