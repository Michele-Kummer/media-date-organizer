"""Every step that changes files only previews unless --apply is given
(US-26, US-27). Run with: py -m unittest discover tests -v"""

import datetime
import hashlib
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from test_smoke import make_image, names, organize, run

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / 'skills' / 'media-date-organizer' / 'scripts'

# Every organize.py phase that changes files, with its flag
CHANGING = {
    'fix_extensions': '--fix-extensions',
    'move_junk': '--move-junk',
    'move_incomplete': '--move-incomplete',
    'quarantine_ads': '--quarantine-ads',
    'fill_blanks': '--fill-blanks',
    'convert_png': '--convert-png',
    'convert_bmp': '--convert-bmp',
    'apply_moves': '--apply-moves',
    'sync_timestamps': '--sync-timestamps',
    'flatten': '--flatten',
    'final_check': '--final-check',
}


def build(root):
    """A folder that gives every changing phase something to do."""
    day = root / '2020-01-01'
    make_image(day / 'right.jpg', taken=datetime.datetime(2020, 1, 1, 10, 0, 0))
    make_image(day / 'wrong.jpg', taken=datetime.datetime(2020, 1, 2, 9, 0, 0))   # move, sync
    make_image(day / 'undated.jpg')                                              # fill blanks
    make_image(day / 'shot.png', fmt='PNG')                                      # convert
    make_image(day / 'scan.bmp', fmt='BMP')                                      # convert BMP
    make_image(day / 'misnamed.gif', fmt='PNG')                                  # fix extensions
    make_image(day / '0c4cda27-b4cc-4e92-a446-d6b780f24a64.jpg')                 # ad
    (day / 'empty.jpg').write_bytes(b'')                                         # incomplete
    (day / 'IMG_1.AAE').write_text('<plist/>')                                   # junk
    (day / 'Thumbs.db').write_bytes(b'\0cache')                                  # junk
    (root / 'media_audit_2019-05-05.xlsx').write_bytes(b'old workbook')          # final check renames
    (root / 'Empty' / 'Inner').mkdir(parents=True)                               # flatten sets aside


def snapshot(root):
    """Every file and folder under root, with its content and timestamps,
    leaving out today's audit workbook (each run, dry runs too, records
    itself there)."""
    today = f"media_audit_{datetime.date.today():%Y-%m-%d}.xlsx"
    state = {}
    for p in sorted(root.rglob('*')):
        if p.name.endswith(today):
            continue
        st = p.stat()
        if p.is_dir():
            state[str(p.relative_to(root))] = 'dir'
        else:
            created = getattr(st, 'st_birthtime', st.st_ctime)
            state[str(p.relative_to(root))] = (hashlib.sha256(p.read_bytes()).hexdigest(),
                                               st.st_mtime_ns, round(created, 3))
    return state


class DryRunTests(unittest.TestCase):

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def fresh(self, name):
        root = self.tmp / name
        root.mkdir()
        build(root)
        return root

    def test_every_changing_phase_is_listed(self):
        # A new phase must be added to CHANGING (and so get a dry run) or be
        # a report that changes nothing
        self.assertEqual(set(organize.PHASE_ORDER) - set(organize.REPORT_PHASES), set(CHANGING))

    def test_every_phase_changes_nothing_without_apply(self):
        for phase, flag in CHANGING.items():
            with self.subTest(phase=phase):
                root = self.fresh(phase)
                before = snapshot(root)
                code, out = run(root, flag)
                self.assertEqual(code, 0, out)
                self.assertEqual(snapshot(root), before, f'{flag} without --apply changed files:\n{out}')
                self.assertIn(f'"{phase}_dry_run"', out)
                self.assertIn('WOULD', out, f'{flag} should list what it would do')
                self.assertIn('Run the same command again with --apply', out)

                # And with --apply it does change something, so the check
                # above is not passing on a folder with nothing to do
                code, out = run(root, flag, '--apply')
                self.assertEqual(code, 0, out)
                self.assertNotEqual(snapshot(root), before, f'{flag} --apply changed nothing:\n{out}')
                self.assertNotIn('DRY RUN', out)

    def test_all_steps_together_preview_without_apply(self):
        root = self.fresh('all')
        before = snapshot(root)
        code, out = run(root, '--all', '--quarantine-ads', '--flatten')
        self.assertEqual(code, 0, out)
        self.assertEqual(snapshot(root), before, out)
        for phase in organize.ALL_PHASES + ('quarantine_ads', 'flatten'):
            self.assertIn(f'"{phase}_dry_run"', out)
        self.assertIn('Summary of this run', out)

    def test_dry_run_lines_match_what_apply_does(self):
        root = self.fresh('match')
        day = root / '2020-01-01'
        _, preview = run(root, '--convert-png')
        self.assertIn('WOULD CONVERT: ' + os.path.join('2020-01-01', 'shot.png') + ' -> shot.jpg', preview)
        self.assertNotIn('shot.jpg', names(day))

        _, preview = run(root, '--sync-timestamps')
        self.assertIn('WOULD SYNC 2020-01-01 10:00:00', preview)

        _, preview = run(root, '--apply-moves')
        self.assertIn(f"WOULD MOVE: {os.path.join('2020-01-01', 'wrong.jpg')} -> "
                      f"{os.path.join('2020-01-02', 'wrong.jpg')}", preview)
        self.assertFalse((root / '2020-01-02').exists(), 'a dry run must not make the target folder')
        _, applied = run(root, '--apply-moves', '--apply')
        self.assertIn(f"MOVED: {os.path.join('2020-01-01', 'wrong.jpg')}", applied)
        self.assertIn('wrong.jpg', names(root / '2020-01-02'))

    def test_dry_run_flag_still_works_and_cannot_be_combined_with_apply(self):
        root = self.fresh('flags')
        before = snapshot(root)
        code, out = run(root, '--flatten', '--dry-run')
        self.assertEqual(code, 0)
        self.assertEqual(snapshot(root), before)
        with self.assertRaises(SystemExit):
            run(root, '--flatten', '--dry-run', '--apply')

    def test_report_phases_run_the_same_without_apply(self):
        root = self.fresh('reports')
        before = snapshot(root)
        for flag in ('--report-only', '--compare-collisions', '--opposite-type'):
            code, out = run(root, flag)
            self.assertEqual(code, 0, out)
            self.assertNotIn('DRY RUN', out, f'{flag} only reports, so has nothing to apply')
        self.assertEqual(snapshot(root), before)

    def test_dry_run_does_not_rename_an_old_audit_workbook(self):
        # BUG-05: working out today's workbook name renamed an old-style one
        root = self.fresh('2014')
        plain = f"media_audit_{datetime.date.today():%Y-%m-%d}.xlsx"
        (root / plain).write_bytes(b'')
        run(root, '--flatten')
        self.assertIn(plain, os.listdir(root), 'a dry run must not rename the audit workbook')
        run(root, '--flatten', '--apply')
        self.assertNotIn(plain, os.listdir(root))
        self.assertIn('2014_photos_' + plain, os.listdir(root))


def powershell():
    for exe in ('pwsh', 'powershell'):
        if shutil.which(exe):
            return shutil.which(exe)
    return None


@unittest.skipUnless(os.name == 'nt' and powershell(), 'needs PowerShell on Windows')
class PowerShellDryRunTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def ps(self, script, *args):
        r = subprocess.run([powershell(), '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                            str(SCRIPTS / script), '-Path', str(self.root), *args],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def test_cleanup_previews_unless_apply(self):
        (self.root / 'empty').mkdir()
        out = self.ps('Cleanup-Pictures.ps1')
        self.assertTrue((self.root / 'empty').is_dir(), 'a preview must not move folders')
        self.assertIn('-Apply', out)
        self.ps('Cleanup-Pictures.ps1', '-Apply')
        self.assertFalse((self.root / 'empty').exists())
        self.assertTrue((self.root / '_empty_folders' / 'empty').is_dir())

    def test_cleanup_reports_media_from_a_different_year(self):
        year = self.root / '2020'
        make_image(year / 'right.jpg', taken=datetime.datetime(2020, 5, 1, 10, 0, 0))
        make_image(year / 'early.jpg', taken=datetime.datetime(2019, 12, 31, 23, 0, 0))
        r = subprocess.run([powershell(), '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                            str(SCRIPTS / 'Cleanup-Pictures.ps1'), '-Path', str(year)],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('OTHER YEAR (2019): early.jpg', r.stdout)
        self.assertIn('Media from a different year : 1', r.stdout)


if __name__ == '__main__':
    unittest.main()
