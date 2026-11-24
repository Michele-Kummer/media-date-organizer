"""Tests for sample-data/generate.py: the Before folder holds every problem,
and running the tool on After fixes each one.

Run from the repository root:
    py -m unittest discover tests -v
"""
import datetime
import importlib.util
import pathlib
import shutil
import tempfile
import unittest

from test_smoke import date_taken, names

GENERATE = pathlib.Path(__file__).resolve().parents[1] / 'sample-data' / 'generate.py'
_spec = importlib.util.spec_from_file_location('generate', GENERATE)
generate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generate)

# Without ExifTool the video whose date is only in its name gets no Media
# Created, so it is rightly left in its day folder instead of flattened
EXIFTOOL = generate.organize._find_exiftool()
UNDATED_VIDEO = 'vid_20240704_201500.mp4'


class SampleDataTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.out = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        cls.before, cls.after = cls.out / 'Before', cls.out / 'After'
        cls.skipped = generate.make_before(cls.before)
        cls.code, cls.log = generate.make_after(cls.before, cls.after)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out, ignore_errors=True)

    def test_before_holds_every_sample(self):
        for rel, *_ in generate.SAMPLES:
            if rel not in self.skipped:
                self.assertTrue((self.before / rel).is_file(), rel)

    def test_before_starts_with_the_problems(self):
        self.assertIsNone(date_taken(self.before / '2024' / '2024-07-04' / 'IMG_20240704_183012.jpg'))
        self.assertIsNone(date_taken(self.before / '2023' / 'Aug 19 2023' / 'Party.jpg'))
        # The extension lies
        self.assertEqual(generate.organize.detect_type(str(self.before / '2024' / '2024-07-04' / 'Beach.PNG')),
                         '.jpg')

    def test_the_tool_runs_cleanly_on_after(self):
        self.assertEqual(self.code, 0, self.log)

    def test_after_has_the_dates_written(self):
        self.assertEqual(date_taken(self.after / '2024' / 'IMG_20240704_183012.jpg'),
                         datetime.datetime(2024, 7, 4, 18, 30, 12))
        self.assertEqual(date_taken(self.after / '2023' / 'Party.jpg').date(), datetime.date(2023, 8, 19))
        self.assertTrue((self.after / '2024' / 'Fireworks.jpg').is_file(), 'PNG converted to JPEG')
        self.assertTrue((self.after / '2024' / 'Beach.JPG').is_file(), 'extension corrected')

    def test_after_flattens_good_photos_into_their_year_folder(self):
        for year in ('2023', '2024'):
            days = [d.name for d in (self.after / year).iterdir()
                    if d.is_dir() and not d.name.startswith('_')]
            if year == '2024' and not EXIFTOOL:
                self.assertEqual(days, ['2024-07-04'], self.log)
                self.assertEqual(names(self.after / year / '2024-07-04'), [UNDATED_VIDEO], self.log)
                continue
            self.assertEqual(days, [], f'{year} should have no day folders left\n{self.log}')
        self.assertEqual([n for n in names(self.after / '2023') if n.endswith('.jpg')], ['cake.jpg', 'party.jpg'])
        # Filed under the import date, taken on New Year's Day: still in 2024
        self.assertIn('img_0412.jpg', names(self.after / '2024'))
        self.assertIn('img_0413.jpg', names(self.after / '2024'))

    def test_after_sets_clutter_aside_in_each_year_and_deletes_nothing(self):
        self.assertEqual(names(self.after / '2023' / '_ads'), ['scribble2mammoth_over@2x_2023-08-19.png'])
        self.assertEqual(len(names(self.after / '2024' / '_ads')), 2)
        self.assertEqual(names(self.after / '2024' / '_junk'), ['._img_0412.jpg', 'img_0412.aae', 'thumbs.db'])
        self.assertEqual(names(self.after / '2024' / '_thumbnails'), ['46.jpg', '47.jpg'])
        self.assertEqual(names(self.after / '2024' / '_incomplete'), ['img_0420_2024-01-15.jpg'])
        # Emptied day folders are moved aside, not deleted
        emptied = names(self.after / '2024' / '_empty_folders')
        if EXIFTOOL:
            self.assertIn('2024-07-04', emptied, self.log)
        else:
            self.assertNotIn('2024-07-04', emptied, 'still holds the undated video')
        self.assertIn('2024-01-15', emptied, self.log)

    def test_comparison_lists_both_folders(self):
        text = generate.comparison(self.before, self.after)
        self.assertIn('## Before', text)
        self.assertIn('## After', text)
        self.assertIn('| `2024/IMG_0412.JPG` | JPG | 2024-01-01 00:05 |', text)


class SetAsideTests(unittest.TestCase):

    def test_an_earlier_run_is_moved_to_previous_not_deleted(self):
        out = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, out, ignore_errors=True)
        (out / 'Before').mkdir()
        (out / 'Before' / 'keep.txt').write_text('mine')
        generate._set_aside(out / 'Before')
        self.assertFalse((out / 'Before').exists())
        kept = list((out / '_previous').glob('Before_*/keep.txt'))
        self.assertEqual(len(kept), 1)
        self.assertNotIn(' ', kept[0].parent.name)


class NameUpgradeTests(unittest.TestCase):
    """US-49: output written while the names had spaces is moved to the new
    names, never deleted."""

    def setUp(self):
        self.base = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.legacy = self.base / 'Sample Pictures'
        self.out = self.base / 'Sample_Pictures'

    def test_the_default_names_have_no_spaces(self):
        self.assertNotIn(' ', generate.DEFAULT_OUT.name)

    def test_legacy_output_is_moved_to_the_new_names(self):
        (self.legacy / 'Before').mkdir(parents=True)
        (self.legacy / 'Before' / 'keep.txt').write_text('mine')
        (self.legacy / 'After log.txt').write_text('log')
        (self.legacy / '_previous' / 'After 2026-11-08 101500').mkdir(parents=True)

        generate._upgrade_names(self.out, self.legacy)

        self.assertFalse(self.legacy.exists())
        self.assertEqual((self.out / 'Before' / 'keep.txt').read_text(), 'mine')
        self.assertFalse((self.out / 'After log.txt').exists())
        previous = sorted(p.name for p in (self.out / '_previous').iterdir())
        self.assertIn('After_2026-11-08_101500', previous)
        self.assertEqual(len([n for n in previous if n.startswith('After_log_')]), 1)
        self.assertFalse(any(' ' in n for n in previous), previous)

    def test_legacy_output_is_left_alone_when_the_new_folder_exists(self):
        (self.legacy / 'Before').mkdir(parents=True)
        self.out.mkdir()
        generate._upgrade_names(self.out, self.legacy)
        self.assertTrue((self.legacy / 'Before').is_dir())

    def test_a_name_already_taken_in_previous_is_left_as_it_is(self):
        (self.out / '_previous' / 'Before 1').mkdir(parents=True)
        (self.out / '_previous' / 'Before_1').mkdir()
        generate._upgrade_names(self.out)
        self.assertTrue((self.out / '_previous' / 'Before 1').is_dir())


if __name__ == '__main__':
    unittest.main()
