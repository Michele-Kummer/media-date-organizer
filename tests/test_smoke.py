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
        self.assertIn(f'{self.root.name}_photos_media_audit_{datetime.date.today():%Y-%m-%d}.xlsx'.lower(),
                      names(self.root))

    def test_folder_names_in_common_date_formats_are_read(self):
        noon = lambda y, m, d: datetime.datetime(y, m, d, 12, 0, 0)
        for folder, want in [
            ('2019-08-30', noon(2019, 8, 30)),
            ('2019_08_30', noon(2019, 8, 30)),
            ('20190830', noon(2019, 8, 30)),
            ('2026-08-19 11-44-31', noon(2026, 8, 19)),
            ('08-19-2026', noon(2026, 8, 19)),
            ('8.19.2026', noon(2026, 8, 19)),
            ('Trip 11-11-2019', noon(2019, 11, 11)),
            ('30-08-2019', noon(2019, 8, 30)),       # not a month first, so day first
            ('Aug 19 2026', noon(2026, 8, 19)),
            ('August 19, 2026', noon(2026, 8, 19)),
            ('19 August 2026', noon(2026, 8, 19)),
            ('2014', None),
            ('2013 West', None),
            ('Day 1', None),
        ]:
            self.assertEqual(organize._folder_name_date(folder), want, folder)

    def test_apply_moves_reads_folder_dates_with_a_time_or_month_first(self):
        taken = datetime.datetime(2024, 8, 28, 10, 19, 44)
        make_image(self.root / '2026-08-19 11-44-31' / 'a.jpg', taken=taken)
        make_image(self.root / '08-28-2024' / 'b.jpg', taken=taken)

        plan = {r['current_name']: r for r in organize.scan(str(self.root))}

        self.assertEqual(plan['a.jpg']['action'], 'move')
        self.assertEqual(plan['a.jpg']['target_folder'], '2024-08-28')
        self.assertEqual(plan['b.jpg']['action'], 'keep')

    def test_report_and_apply_moves_look_at_every_depth(self):
        aug30, aug31 = datetime.datetime(2019, 8, 30, 10, 0, 0), datetime.datetime(2019, 8, 31, 10, 0, 0)
        make_image(self.root / 'loose.jpg', taken=aug30)
        make_image(self.root / '2019-08-30' / 'wrong.jpg', taken=aug31)
        make_image(self.root / 'Trip' / '2019-08-30' / 'deep.jpg', taken=aug31)
        make_image(self.root / 'Trip' / '2019-08-30' / 'right.jpg', taken=aug30)
        make_image(self.root / 'Trip' / '2019-08-30' / 'undated.jpg')
        make_image(self.root / '_ads' / '2019-08-30' / 'ad.jpg', taken=aug31)

        plan = {r['current_name']: r for r in organize.scan(str(self.root))}

        self.assertEqual(sorted(plan), ['deep.jpg', 'loose.jpg', 'right.jpg', 'undated.jpg', 'wrong.jpg'])
        self.assertEqual((plan['loose.jpg']['current_folder'], plan['loose.jpg']['action']), ('.', 'keep'))
        self.assertEqual(plan['wrong.jpg']['target_folder'], '2019-08-31')
        # A deep file moves to a sibling of its own folder, not up to root
        self.assertEqual(plan['deep.jpg']['current_folder'], 'Trip/2019-08-30')
        self.assertEqual(plan['deep.jpg']['target_folder'], 'Trip/2019-08-31')
        self.assertEqual(plan['right.jpg']['action'], 'keep')
        self.assertEqual(plan['undated.jpg']['new_name'], 'undated_2019-08-30.jpg')

        code, _ = run(self.root, '--apply-moves', '--apply')

        self.assertEqual(code, 0)
        self.assertEqual(names(self.root / '2019-08-31'), ['wrong.jpg'])
        self.assertEqual(names(self.root / 'Trip' / '2019-08-31'), ['deep.jpg'])
        self.assertEqual(names(self.root / 'Trip' / '2019-08-30'), ['right.jpg', 'undated_2019-08-30.jpg'])
        self.assertIn('loose.jpg', names(self.root))
        self.assertEqual(names(self.root / '_ads' / '2019-08-30'), ['ad.jpg'])

    def test_a_file_loose_in_a_dated_root_is_never_moved_out(self):
        day = self.root / '2019-08-30'
        make_image(day / 'right.jpg', taken=datetime.datetime(2019, 8, 30, 10, 0, 0))
        make_image(day / 'other_day.jpg', taken=datetime.datetime(2019, 9, 1, 10, 0, 0))

        plan = {r['current_name']: r for r in organize.scan(str(day))}

        self.assertEqual(plan['right.jpg']['action'], 'keep')
        self.assertEqual(plan['other_day.jpg']['action'], 'in-root-date-differs')

        code, _ = run(day, '--apply-moves')

        self.assertEqual(code, 0)
        self.assertEqual([n for n in names(day) if n.endswith('.jpg')], ['other_day.jpg', 'right.jpg'])
        self.assertEqual(names(self.root), ['2019-08-30'])

    def test_all_cleans_dates_converts_and_moves(self):
        day = self.root / '2020-01-01'
        make_image(day / 'wrong.jpg', taken=datetime.datetime(2020, 2, 2, 9, 30, 0))
        make_image(day / 'IMG_20210304_101112.jpg')           # no Date Taken, date in the name
        make_image(day / 'shot.png', taken=datetime.datetime(2020, 1, 1, 8, 0, 0))
        (day / 'empty.jpg').write_bytes(b'')                   # a failed copy
        (day / 'IMG_0001.AAE').write_text('edit sidecar')
        (day / 'Thumbs.db').write_bytes(b'cache')

        code, _ = run(self.root, '--all', '--apply')

        self.assertEqual(code, 0)
        # Junk and the incomplete file set aside, nothing deleted
        self.assertNotIn('img_0001.aae', names(day))
        self.assertNotIn('thumbs.db', names(day))
        self.assertEqual(names(self.root / '_junk' / '2020-01-01'), ['img_0001.aae', 'thumbs.db'])
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

    def test_fill_blanks_looks_in_root_and_every_subfolder(self):
        stamp = datetime.datetime(2021, 3, 4, 10, 11, 12)
        in_root = self.root / 'IMG_20210304_101112.jpg'
        one_down = self.root / 'Trip' / 'IMG_20210304_101112.jpg'
        deep = self.root / 'Trip' / 'Day 1' / 'Beach' / 'IMG_20210304_101112.jpg'
        by_folder = self.root / 'Trip' / '2020-01-01' / 'undated.jpg'
        for p in (in_root, one_down, deep, by_folder):
            make_image(p)
        make_image(self.root / '_ads' / 'IMG_20210304_101112.jpg')   # holding folders are left alone

        code, out = run(self.root, '--fill-blanks')
        self.assertEqual(code, 0)
        self.assertIn('WOULD WRITE', out)
        self.assertIsNone(date_taken(deep), 'a dry run must not write anything')

        code, _ = run(self.root, '--fill-blanks', '--apply')

        self.assertEqual(code, 0)
        for p in (in_root, one_down, deep):
            self.assertEqual(date_taken(p), stamp)
        self.assertEqual(date_taken(by_folder), datetime.datetime(2020, 1, 1, 12, 0, 0))
        self.assertIsNone(date_taken(self.root / '_ads' / 'IMG_20210304_101112.jpg'))

    def test_opposite_type_reports_photos_among_videos_by_year_folder(self):
        for rel in ('2014/7-17-2014/a.avi', '2014/b.mp4', '2015/c.mov', '2015/2015-03-01/d.mp4'):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'video data')
        make_image(self.root / '2014' / '7-17-2014' / 'stray.jpg')
        make_image(self.root / '2014' / '_ads' / 'ad.jpg')       # holding folders are not counted
        make_image(self.root / 'Wedding' / 'guest.jpg')          # not a year folder
        before = sorted(str(p) for p in self.root.rglob('*'))

        code, out = run(self.root, '--opposite-type')

        self.assertEqual(code, 0)
        self.assertIn('PHOTO IN VIDEO FOLDER: 2014/7-17-2014/stray.jpg', out)
        self.assertNotIn('ad.jpg', out)
        self.assertNotIn('guest.jpg', out)
        self.assertIn('2014: 1 photo(s), 2 video(s)', out)
        self.assertIn('2015: 0 photo(s), 2 video(s)', out)
        self.assertIn('"photos-in-video-folders": 1', out)
        after = sorted(str(p) for p in self.root.rglob('*') if p.suffix != '.xlsx')
        self.assertEqual(after, before, 'a report must not move anything')

    def test_other_year_counts_media_taken_in_another_year(self):
        year = self.root / '2020'
        make_image(year / 'right.jpg', taken=datetime.datetime(2020, 5, 1, 10, 0, 0))
        make_image(year / 'Trip' / 'early.jpg', taken=datetime.datetime(2019, 12, 31, 23, 0, 0))
        make_image(year / 'late.jpg', taken=datetime.datetime(2021, 1, 1, 9, 0, 0))
        make_image(year / 'undated.jpg')
        make_image(year / '_ads' / 'ad.jpg', taken=datetime.datetime(2018, 1, 1, 9, 0, 0))
        before = sorted(str(p) for p in self.root.rglob('*'))

        code, out = run(year, '--other-year')

        self.assertEqual(code, 0)
        self.assertIn('OTHER YEAR (2019): Trip/early.jpg', out)
        self.assertIn('OTHER YEAR (2021): late.jpg', out)
        self.assertNotIn('ad.jpg', out)
        self.assertIn('OTHER YEAR: 2 of 4 media item(s) are from a different year (2019: 1, 2021: 1); '
                      '1 have no Date Taken', out)
        after = sorted(str(p) for p in self.root.rglob('*') if p.suffix != '.xlsx')
        self.assertEqual(after, before, 'a report must not move anything')

        # Given the folder holding the year folders, each is checked against its own year
        _, out = run(self.root, '--other-year')
        self.assertIn('OTHER YEAR (2019): 2020/Trip/early.jpg', out)
        self.assertIn('2020: 2 from another year', out)

    def test_final_check_reports_what_is_left_by_year_folder(self):
        for rel in ('2014/a.mp4', '2014/7-17-2014/b.avi', '2015/c.mov'):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'video data')
        make_image(self.root / '2014' / 'stray.jpg')
        # Name clashes as --flatten leaves them: a copy renamed with its date,
        # and another file of the same name left in its subfolder
        (self.root / '2014' / 'a_2014-07-17.mp4').write_bytes(b'video data')
        (self.root / '2014' / '7-17-2014' / 'a.mp4').write_bytes(b'another video')
        make_image(self.root / '2014' / '_ads' / 'ad1.jpg')
        make_image(self.root / '2014' / '_ads' / 'ad2.jpg')
        (self.root / '2014' / '_incomplete' / '2014-01-01').mkdir(parents=True)
        (self.root / '2014' / '_incomplete' / '2014-01-01' / 'empty.mp4').write_bytes(b'')
        (self.root / '2014' / 'media_audit_2020-01-01.xlsx').write_bytes(b'an earlier audit')
        before = sorted(str(p) for p in self.root.rglob('*'))

        code, out = run(self.root, '--final-check')

        self.assertEqual(code, 0)
        self.assertIn('IN ADS: 2014/_ads (2 file(s))', out)
        self.assertIn('INCOMPLETE: 2014/_incomplete (1 file(s))', out)
        self.assertIn('PHOTO IN VIDEO FOLDER: 2014/stray.jpg', out)
        self.assertIn('NOT FLATTENED: 2014/7-17-2014 (2 file(s))', out)
        renamed = 'AUDIT FILE: 2014/media_audit_2020-01-01.xlsx -> 2014_videos_media_audit_2020-01-01.xlsx'
        self.assertIn('WOULD RENAME ' + renamed, out)
        self.assertIn('COLLISION, identical files (renamed with a date): 2014/a_2014-07-17.mp4 | 2014/a.mp4', out)
        self.assertIn('COLLISION, different files (left in its subfolder): 2014/7-17-2014/a.mp4 | 2014/a.mp4', out)
        self.assertIn('2014: 2 in _ads, 1 in _incomplete, 0 in _junk, 1 photo(s) among videos, '
                      '1 folder(s) not flattened, 3 collision(s), 1 audit file(s)', out)
        self.assertIn('3 collision(s) (1 identical, 2 different)', out)
        self.assertIn('2015: clean', out)
        self.assertIn('1 of 2 year folder(s) have something left', out)
        # This run's own workbook, in the root, is the only new file
        after = sorted(str(p) for p in self.root.rglob('*') if p.parent != self.root)
        self.assertEqual(after, [p for p in before if pathlib.Path(p).parent != self.root],
                         'a dry run must not change anything')
        own = f'{self.root.name}_videos_media_audit_{datetime.date.today():%Y-%m-%d}.xlsx'.lower()
        self.assertIn(own, names(self.root), 'the workbook is named for its folder and media type')
        self.assertNotIn('audit file: ' + own, out.lower(), "this run's own workbook is not a leftover")

        code, out = run(self.root, '--final-check', '--apply')

        # The one change a real run makes: the leftover workbook gets its prefix
        self.assertEqual(code, 0)
        self.assertIn('RENAMED ' + renamed, out)
        self.assertIn('2014_videos_media_audit_2020-01-01.xlsx', names(self.root / '2014'))
        self.assertNotIn('media_audit_2020-01-01.xlsx', names(self.root / '2014'))

    def test_mac_sidecars_do_not_stop_convert_and_are_moved_aside_as_junk(self):
        day = self.root / '2020-01-01'
        make_image(day / 'shot.png')
        (day / '._shot.png').write_bytes(organize.APPLEDOUBLE_MAGIC + b'\x00' * 60)
        make_image(day / '._real.png')                         # a picture, despite the name

        code, out = run(self.root, '--convert-png', '--apply')
        self.assertEqual(code, 0)
        self.assertIn('FAILED to convert', out)
        self.assertIn('shot.jpg', os.listdir(day), 'the new JPEG gets a lowercase extension')
        self.assertNotIn('._shot.jpg', names(day))

        code, _ = run(self.root, '--move-junk')
        self.assertEqual(code, 0)
        self.assertIn('._shot.png', names(day), 'a dry run must not move anything')

        code, _ = run(self.root, '--move-junk', '--apply')
        self.assertEqual(code, 0)
        self.assertNotIn('._shot.png', names(day))
        self.assertEqual(names(self.root / '_junk' / '2020-01-01'), ['._shot.png'])
        self.assertIn('._real.png', names(day))
        self.assertIn('shot.png', names(day))

    def test_apply_moves_suffixes_only_undated_files_and_strips_nothing(self):
        day = self.root / '2020-01-01'
        make_image(day / 'dated_2019-05-05.jpg', taken=datetime.datetime(2020, 1, 1, 10, 0, 0))
        make_image(day / 'undated.jpg')
        make_image(day / 'already_2020-01-01.jpg')
        make_image(day / 'stray.jpeg', taken=datetime.datetime(2020, 2, 2, 9, 30, 0))

        code, _ = run(self.root, '--apply-moves', '--apply')

        self.assertEqual(code, 0)
        # Exact names: the extension keeps its spelling and its case
        self.assertEqual(sorted(os.listdir(day)),
                         ['already_2020-01-01.jpg', 'dated_2019-05-05.jpg', 'undated_2020-01-01.jpg'])
        self.assertEqual(os.listdir(self.root / '2020-02-02'), ['stray.jpeg'])

    @unittest.skipUnless(os.name == 'nt', 'Date Created can only be set on Windows')
    def test_sync_sets_date_created_on_edited_files_but_keeps_their_modified(self):
        taken = datetime.datetime(2020, 1, 1, 10, 0, 0)
        plain = self.root / '2020-01-01' / 'plain.jpg'
        edited = self.root / '2020-01-01' / 'edited.jpg'
        in_root = self.root / 'in_root.jpg'
        deep = self.root / 'Trip' / 'Day 1' / 'Beach' / 'deep.jpg'
        for p in (plain, edited, in_root, deep):
            make_image(p, taken=taken)
        with Image.open(edited) as img:
            exif = img.getexif()
            exif[0x0132] = '2021-06-06 08:00:00'.replace('-', ':')   # EXIF DateTime: edited later
            img.save(edited, exif=exif)
        self.assertEqual(date_taken(edited), taken)
        modified = os.stat(edited).st_mtime

        code, out = run(self.root, '--sync-timestamps', '--apply')

        self.assertEqual(code, 0)
        self.assertIn('created only (edited)', out)
        for p in (plain, edited, in_root, deep):
            self.assertEqual(datetime.datetime.fromtimestamp(os.stat(p).st_birthtime), taken)
        for p in (plain, in_root, deep):
            self.assertEqual(datetime.datetime.fromtimestamp(os.stat(p).st_mtime), taken)
        self.assertEqual(os.stat(edited).st_mtime, modified)

    def test_quarantine_ads_moves_only_ad_names(self):
        day = self.root / '2020-01-01'
        ads = ['0c4cda27-b4cc-4e92-a446-d6b780f24a64.jpg',
               '54ac2fda0a6755305200011c-b30-600.jpg',
               '55d58970f6cd4574f635d6e3_568-1443241239.jpg']
        for name in ads:
            make_image(day / name)
        make_image(day / 'IMG_20200101_120000.jpg')

        code, out = run(self.root, '--quarantine-ads')
        self.assertEqual(code, 0)
        self.assertEqual(len(names(day)), 4, 'a dry run must not move anything')
        self.assertIn('WOULD', out)

        code, _ = run(self.root, '--quarantine-ads', '--apply')
        self.assertEqual(code, 0)
        self.assertEqual(names(day), ['img_20200101_120000.jpg'])
        self.assertEqual(names(self.root / '_ads' / '2020-01-01'), sorted(ads))

    def test_flatten_moves_dated_files_up_and_keeps_undated(self):
        make_image(self.root / '2020-01-01' / 'a.jpg', taken=datetime.datetime(2020, 1, 1, 10, 0, 0))
        make_image(self.root / '2020-01-02' / 'a.jpg', color=(0, 0, 200),
                   taken=datetime.datetime(2020, 1, 2, 10, 0, 0))
        make_image(self.root / 'misc' / 'undated.jpg')

        (self.root / 'clip.mp4').write_bytes(b'not read: only the extension is counted')

        code, out = run(self.root, '--flatten')
        self.assertEqual(code, 0)
        self.assertIn('OPPOSITE TYPE: 1 video(s) in this photo folder (2 photo(s)) once flattened', out)

        code, out = run(self.root, '--flatten', '--apply')

        self.assertEqual(code, 0)
        self.assertIn('OPPOSITE TYPE: 1 video(s) in this photo folder (2 photo(s))', out)
        self.assertIn('"videos-in-photo-folder": 1', out)
        # Same name from two days: the second gets its date as a suffix
        self.assertIn('a.jpg', names(self.root))
        self.assertIn('a_2020-01-02.jpg', names(self.root))
        self.assertFalse((self.root / '2020-01-01').exists())
        self.assertFalse((self.root / '2020-01-02').exists())
        # Emptied folders are set aside, not deleted
        self.assertEqual(names(self.root / '_empty_folders'), ['2020-01-01', '2020-01-02'])
        self.assertEqual(names(self.root / 'misc'), ['undated.jpg'])

    def test_flatten_moves_undated_ads_up_into_ads(self):
        ads = self.root / '_ads'
        make_image(ads / '2020-01-01' / 'ad.jpg')
        make_image(ads / '2020-01-02' / 'ad.jpg', color=(0, 0, 200))

        code, out = run(self.root, '--flatten', '--apply')

        self.assertEqual(code, 0)
        # Same name from two folders: the second gets its folder name as a suffix
        self.assertEqual(names(ads), ['ad.jpg', 'ad_2020-01-02.jpg'])
        self.assertEqual(names(self.root / '_empty_folders' / '_ads'), ['2020-01-01', '2020-01-02'])
        self.assertIn('"ads-moved": 2', out)

    def test_flatten_with_ads_folder_as_root_moves_undated_ads_up(self):
        # Laid out as --quarantine-ads leaves it: the subfolder path is kept,
        # so ads sit two levels down
        ads = self.root / '_ads'
        make_image(ads / 'Temp' / '2020-01-01' / 'ad.jpg')
        make_image(ads / 'Temp' / '2020-01-02' / 'ad.jpg', color=(0, 0, 200))
        (ads / 'Temp' / '2020-01-02' / 'draw_title.raw').write_bytes(b'\0' * 64)

        # A trailing separator must not stop the emptied folders being found
        code, out = run(str(ads) + os.sep, '--flatten')
        self.assertEqual(code, 0)
        self.assertIn('WOULD MOVE: _ads/Temp/2020-01-01/ad.jpg -> _ads/ad.jpg', out)
        self.assertIn('WOULD MOVE: _ads/Temp/2020-01-02/ad.jpg -> _ads/ad_2020-01-02.jpg', out)
        self.assertIn('WOULD MOVE EMPTY', out)
        self.assertNotIn('LEFT', out)
        self.assertTrue((ads / 'Temp' / '2020-01-01' / 'ad.jpg').exists(), 'a dry run must not move anything')

        code, out = run(ads, '--flatten', '--apply')

        self.assertEqual(code, 0)
        self.assertEqual([n for n in names(ads) if not n.endswith('.xlsx')],
                         ['ad.jpg', 'ad_2020-01-02.jpg', 'draw_title.raw'])
        # Emptied folders go beside _ads, as from a run on its parent
        self.assertEqual(names(self.root / '_empty_folders' / '_ads'), ['temp'])
        self.assertFalse((ads / 'Temp').exists())
        self.assertFalse((ads / '_empty_folders').exists())

    def test_flatten_moves_nested_empty_folders_aside_once_and_never_overwrites(self):
        taken = datetime.datetime(2020, 1, 1, 10, 0, 0)
        day = self.root / '2020-01-01'
        make_image(day / 'a.jpg', taken=taken)
        make_image(day / 'b.jpg', taken=taken)
        (day / 'Edits' / 'Old').mkdir(parents=True)
        (self.root / '_empty_folders' / '2020-01-01').mkdir(parents=True)   # from an earlier run

        code, out = run(self.root, '--flatten')
        self.assertEqual(code, 0)
        self.assertIn('WOULD MOVE EMPTY', out)
        self.assertTrue((day / 'a.jpg').exists())

        code, out = run(self.root, '--flatten', '--apply')

        self.assertEqual(code, 0)
        self.assertEqual(sorted(n for n in names(self.root) if n.endswith('.jpg')), ['a.jpg', 'b.jpg'])
        self.assertFalse(day.exists())
        # The whole emptied tree moves as one, beside the earlier one
        moved = self.root / '_empty_folders' / '2020-01-01 (2)'
        self.assertEqual(names(moved), ['edits'])
        self.assertEqual(names(moved / 'Edits'), ['old'])
        self.assertIn('"empty-folders-moved": 3', out)

        # _empty_folders is a holding folder: a second run leaves it alone
        code, out = run(self.root, '--flatten', '--apply')
        self.assertEqual(code, 0)
        self.assertTrue(moved.is_dir())
        self.assertNotIn('MOVED EMPTY', out)

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

        code, out = run(self.root, '--visual-compare')
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
        # It only reports, so --apply changes nothing either
        code, _ = run(self.root, '--visual-compare', '--apply')
        self.assertEqual(code, 0)
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob('*') if p.suffix != '.xlsx'))


if __name__ == '__main__':
    unittest.main()
