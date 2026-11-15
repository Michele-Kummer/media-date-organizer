"""Tests for scripts/Move-IncompleteByYear.ps1: each year folder's
incomplete files go into that year's own _incomplete folder.

Run from the repository root:
    py -m unittest discover tests -v
"""
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from test_smoke import names
from test_transfer_stubs import FULL

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / 'scripts' / 'Move-IncompleteByYear.ps1'
PWSH = shutil.which('pwsh') or shutil.which('powershell')


@unittest.skipUnless(PWSH, 'PowerShell is needed to run the script')
class MoveIncompleteByYearTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        for year in ('2018', '2019'):
            day = self.root / year / f"{year}-05-01"
            day.mkdir(parents=True)
            (day / 'stub.jpg').write_bytes(FULL)
        (self.root / 'Other').mkdir()
        (self.root / 'Other' / 'stub.jpg').write_bytes(FULL)

    def run_script(self, *args):
        return subprocess.run([PWSH, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(SCRIPT),
                               '-Root', str(self.root), *args], capture_output=True, text=True)

    def test_preview_moves_nothing(self):
        result = self.run_script()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('===== 2018 =====', result.stdout)
        self.assertFalse((self.root / '2018' / '_incomplete').exists())

    def test_apply_puts_each_year_in_its_own_incomplete(self):
        result = self.run_script('-Apply')

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(names(self.root / '2018' / '_incomplete'), ['stub_2018-05-01.jpg'])
        self.assertEqual(names(self.root / '2019' / '_incomplete'), ['stub_2019-05-01.jpg'])
        self.assertFalse((self.root / '_incomplete').exists())
        self.assertEqual(names(self.root / 'Other'), ['stub.jpg'], 'folders not named for a year are left alone')


if __name__ == '__main__':
    unittest.main()
