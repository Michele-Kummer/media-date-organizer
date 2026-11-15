"""Tests for placeholder Date Taken values (1904-01-01 00:00:00) and for
photos taken before 1970 (BUG-37).

Run from the repository root:
    py -m unittest discover tests -v
"""
import datetime
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_smoke import date_taken, make_image, organize, run  # noqa: E402

PLACEHOLDER = datetime.datetime(1904, 1, 1, 0, 0, 0)


class PlaceholderDateTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_placeholder_is_read_as_blank(self):
        self.assertIsNone(organize._parse_exif_dt('1904:01:01 00:00:00'))

    def test_dates_near_the_placeholder_are_kept(self):
        self.assertEqual(organize._parse_exif_dt('1904:01:01 00:00:01'),
                         datetime.datetime(1904, 1, 1, 0, 0, 1))
        self.assertEqual(organize._parse_exif_dt('1955:07:04 12:00:00'),
                         datetime.datetime(1955, 7, 4, 12, 0, 0))

    def test_photo_with_placeholder_has_no_date_taken(self):
        photo = self.root / 'VideoCapture_20200614-211024.jpg'
        make_image(photo, taken=PLACEHOLDER)

        self.assertIsNone(date_taken(photo))

    def test_fill_blanks_replaces_placeholder_with_filename_date(self):
        photo = self.root / '2020-06-14' / 'VideoCapture_20200614-211024.jpg'
        make_image(photo, taken=PLACEHOLDER)

        code, out = run(self.root, '--fill-blanks', '--apply')

        self.assertEqual(code, 0, out)
        self.assertEqual(date_taken(photo), datetime.datetime(2020, 6, 14, 21, 10, 24))

    def test_sync_skips_placeholder_instead_of_crashing(self):
        photo = self.root / 'VideoCapture_20200614-211024.jpg'
        make_image(photo, taken=PLACEHOLDER)
        before = os.stat(photo).st_mtime

        counts = organize.sync_timestamps(str(self.root))

        self.assertEqual(counts.get('no-date-taken'), 1)
        self.assertEqual(os.stat(photo).st_mtime, before)


class OldPhotoTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_local_timestamp_matches_python_after_1970(self):
        dt = datetime.datetime(2020, 6, 14, 21, 10, 24)
        self.assertEqual(organize._local_timestamp(dt), dt.timestamp())

    def test_local_timestamp_handles_dates_before_1970(self):
        for dt in (datetime.datetime(1969, 12, 31, 23, 59, 59),
                   datetime.datetime(1955, 7, 4, 12, 0, 0),
                   datetime.datetime(1904, 2, 29, 8, 0, 0),
                   datetime.datetime(1888, 3, 1, 0, 0, 0)):
            with self.subTest(dt=dt):
                naive_utc = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
                # Off from naive UTC by no more than a time zone offset
                self.assertLessEqual(abs(organize._local_timestamp(dt) - naive_utc), 14 * 3600)

    def test_local_timestamp_keeps_order_across_1970(self):
        before = organize._local_timestamp(datetime.datetime(1969, 12, 31, 23, 0, 0))
        after = organize._local_timestamp(datetime.datetime(1970, 1, 2, 0, 0, 0))
        self.assertLess(before, after)

    def test_sync_sets_file_times_on_a_scanned_1955_photo(self):
        taken = datetime.datetime(1955, 7, 4, 12, 0, 0)
        photo = self.root / 'scan.jpg'
        make_image(photo, taken=taken)

        counts = organize.sync_timestamps(str(self.root))

        self.assertEqual(counts.get('failed', 0), 0, counts)
        self.assertEqual(counts.get('synced'), 1, counts)
        self.assertAlmostEqual(os.stat(photo).st_mtime, organize._local_timestamp(taken), delta=1)


class SyncKeepsGoingTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_a_date_that_cannot_be_converted_is_logged_as_failed_and_the_rest_sync(self):
        make_image(self.root / 'bad.jpg', taken=datetime.datetime(2020, 1, 1, 10, 0, 0))
        make_image(self.root / 'good.jpg', taken=datetime.datetime(2020, 1, 2, 10, 0, 0))
        real = organize._local_timestamp

        def fail_on_first_date(dt):
            if dt == datetime.datetime(2020, 1, 1, 10, 0, 0):
                raise OSError(22, 'Invalid argument')
            return real(dt)

        with mock.patch.object(organize, '_local_timestamp', side_effect=fail_on_first_date):
            code, out = run(self.root, '--sync-timestamps', '--apply')

        self.assertEqual(code, 0, out)
        self.assertIn('FAILED bad.jpg', out)
        self.assertIn('SYNCED 2020-01-02 10:00:00: good.jpg', out)


if __name__ == '__main__':
    unittest.main()
