"""Tests that --sync-timestamps leaves files whose times already match their
Date Taken alone, so a second run lists only what changed (BUG-38).

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
from test_smoke import make_image, organize, run  # noqa: E402

TAKEN = datetime.datetime(2020, 6, 14, 21, 10, 24)


class AlreadySyncedTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.photo = self.root / 'Holiday' / 'IMG_0001.jpg'
        make_image(self.photo, taken=TAKEN)
        self.ts = organize._local_timestamp(TAKEN)

    def test_first_run_syncs_the_file(self):
        counts = organize.sync_timestamps(str(self.root))

        self.assertEqual(counts.get('synced'), 1, counts)
        self.assertNotIn('already-synced', counts)

    def test_second_run_counts_the_file_as_already_synced(self):
        organize.sync_timestamps(str(self.root))

        counts = organize.sync_timestamps(str(self.root))

        self.assertEqual(counts, {'already-synced': 1})

    def test_second_run_does_not_list_the_file(self):
        run(self.root, '--sync-timestamps', '--apply')

        code, out = run(self.root, '--sync-timestamps', '--apply')

        self.assertEqual(code, 0, out)
        self.assertNotIn('SYNCED', out)
        self.assertIn('already-synced', out)

    def test_preview_after_a_sync_has_nothing_to_list(self):
        organize.sync_timestamps(str(self.root))

        code, out = run(self.root, '--sync-timestamps')

        self.assertEqual(code, 0, out)
        self.assertNotIn('WOULD SYNC', out)

    def test_preview_before_a_sync_still_lists_the_file(self):
        code, out = run(self.root, '--sync-timestamps')

        self.assertEqual(code, 0, out)
        self.assertIn('WOULD SYNC 2020-06-14 21:10:24', out)

    def test_a_time_within_two_seconds_counts_as_synced(self):
        organize.sync_timestamps(str(self.root))
        # As a FAT32 or exFAT drive would round it
        os.utime(self.photo, (self.ts + 2, self.ts + 2))

        counts = organize.sync_timestamps(str(self.root))

        self.assertEqual(counts, {'already-synced': 1})

    def test_a_time_further_off_is_synced_again(self):
        organize.sync_timestamps(str(self.root))
        os.utime(self.photo, (self.ts + 60, self.ts + 60))

        counts = organize.sync_timestamps(str(self.root))

        self.assertEqual(counts.get('synced'), 1, counts)
        self.assertAlmostEqual(os.stat(self.photo).st_mtime, self.ts, delta=1)

    def test_an_already_synced_file_is_not_written(self):
        organize.sync_timestamps(str(self.root))

        with mock.patch.object(organize.os, 'utime') as utime, \
                mock.patch.object(organize, '_set_creation_time') as set_created:
            organize.sync_timestamps(str(self.root))

        utime.assert_not_called()
        set_created.assert_not_called()


@unittest.skipUnless(os.name == 'nt', 'Date Created can only be set on Windows')
class EditedFileTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.photo = self.root / 'edited.jpg'
        make_image(self.photo, taken=TAKEN)
        patcher = mock.patch.object(organize, '_is_unedited', return_value=False)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_edited_file_is_already_synced_once_date_created_matches(self):
        first = organize.sync_timestamps(str(self.root))
        second = organize.sync_timestamps(str(self.root))

        self.assertEqual(first.get('created-only-edited'), 1, first)
        self.assertEqual(second, {'already-synced': 1})

    def test_edited_files_date_modified_is_not_compared(self):
        organize.sync_timestamps(str(self.root))
        # Edited later: Date Modified moves on, Date Created still matches
        later = organize._local_timestamp(TAKEN) + 86400
        os.utime(self.photo, (later, later))

        counts = organize.sync_timestamps(str(self.root))

        self.assertEqual(counts, {'already-synced': 1})
        self.assertAlmostEqual(os.stat(self.photo).st_mtime, later, delta=1)


class AlreadySyncedHelperTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.file = self.root / 'a.jpg'
        self.file.write_bytes(b'x')

    def test_new_file_does_not_match_an_old_date(self):
        ts = organize._local_timestamp(TAKEN)
        self.assertFalse(organize._already_synced(str(self.file), ts, True))

    def test_edited_file_away_from_windows_never_counts_as_synced(self):
        ts = os.stat(self.file).st_mtime
        with mock.patch.object(organize.os, 'name', 'posix'):
            self.assertFalse(organize._already_synced(str(self.file), ts, False))


if __name__ == '__main__':
    unittest.main()
