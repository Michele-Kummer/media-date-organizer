"""Tests that one photo or video that cannot be read does not stop a step,
and that a step that does stop still leaves a record in the audit workbook
(issue #57, BUG-02 in docs/user-stories-and-bugs.md).

A file locked by another program is simulated by making read_metadata raise
PermissionError for it; one too large to read whole, by MemoryError.

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

from openpyxl import load_workbook

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_smoke import make_image, names, organize, run  # noqa: E402

TAKEN = datetime.datetime(2020, 6, 14, 21, 10, 24)
REAL_READ = organize.read_metadata


def unreadable(bad_name, error):
    """A read_metadata that raises error for the file named bad_name."""
    def read(path, ftype):
        if os.path.basename(path) == bad_name:
            raise error
        return REAL_READ(path, ftype)
    return mock.patch.object(organize, 'read_metadata', side_effect=read)


class UnreadableFileTestCase(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        make_image(self.root / '2020-06-14' / 'locked.jpg', taken=TAKEN)
        make_image(self.root / '2020-06-14' / 'fine.jpg', taken=TAKEN)

    def workbook(self):
        books = [n for n in os.listdir(self.root) if n.endswith('.xlsx')]
        self.assertEqual(len(books), 1, books)
        return load_workbook(self.root / books[0])


class SyncTimestampsTests(UnreadableFileTestCase):

    def test_the_unreadable_file_is_counted_and_the_rest_are_synced(self):
        with unreadable('locked.jpg', PermissionError(13, 'Permission denied')):
            counts = organize.sync_timestamps(str(self.root))

        self.assertEqual(counts, {'read-failed': 1, 'synced': 1})

    def test_a_file_too_large_to_read_is_counted_too(self):
        with unreadable('locked.jpg', MemoryError()):
            counts = organize.sync_timestamps(str(self.root))

        self.assertEqual(counts.get('read-failed'), 1, counts)
        self.assertEqual(counts.get('synced'), 1, counts)

    def test_the_failure_is_reported_and_the_audit_is_written(self):
        with unreadable('locked.jpg', PermissionError(13, 'Permission denied')):
            code, out = run(self.root, '--sync-timestamps', '--apply')

        self.assertEqual(code, 0, out)
        self.assertIn('FAILED to read 2020-06-14/locked.jpg: [Errno 13] Permission denied', out)
        self.assertIn('SYNCED 2020-06-14 21:10:24: 2020-06-14/fine.jpg', out)
        self.assertIn('Run log', self.workbook().sheetnames)


class ScanTests(UnreadableFileTestCase):

    def setUp(self):
        super().setUp()
        make_image(self.root / '2020-06-14' / 'wrong.jpg', taken=datetime.datetime(2020, 6, 15, 8, 0, 0))

    def test_the_unreadable_file_is_listed_as_read_failed(self):
        with unreadable('locked.jpg', PermissionError(13, 'Permission denied')):
            plan = {r['current_name']: r for r in organize.scan(str(self.root))}

        self.assertEqual(plan['locked.jpg']['action'], 'read-failed')
        self.assertEqual(plan['locked.jpg']['target_folder'], '2020-06-14')
        self.assertEqual(plan['fine.jpg']['action'], 'keep')
        self.assertEqual(plan['wrong.jpg']['action'], 'move')

    def test_audit_finishes_and_counts_the_unreadable_file(self):
        with unreadable('locked.jpg', MemoryError()):
            code, out = run(self.root, '--audit')

        self.assertEqual(code, 0, out)
        self.assertIn('FAILED to read 2020-06-14/locked.jpg: MemoryError', out)
        summary = {row[0]: row[1] for row in self.workbook()['Summary'].iter_rows(values_only=True)}
        self.assertEqual(summary['Could not be read'], 1)
        self.assertEqual(summary['Files scanned'], 3)

    def test_apply_moves_leaves_the_unreadable_file_and_moves_the_rest(self):
        with unreadable('locked.jpg', PermissionError(13, 'Permission denied')):
            code, out = run(self.root, '--apply-moves', '--apply')

        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '2020-06-14'), ['fine.jpg', 'locked.jpg'])
        self.assertEqual(names(self.root / '2020-06-15'), ['wrong.jpg'])
        self.assertIn('"skipped-read-failed": 1', out)

    def test_compare_collisions_finishes(self):
        with unreadable('locked.jpg', PermissionError(13, 'Permission denied')):
            code, out = run(self.root, '--compare-collisions')

        self.assertEqual(code, 0, out)


class StepThatStopsTests(UnreadableFileTestCase):
    """A step that stops on an error nobody planned for still leaves a record
    of itself and of the steps before it."""

    def crash(self, *_args):
        raise RuntimeError('something unexpected')

    def test_the_finished_steps_and_the_failure_are_recorded(self):
        with mock.patch.object(organize, 'convert_pngs', side_effect=self.crash):
            code, out = run(self.root, '--all')

        self.assertEqual(code, 1, out)
        self.assertIn('FAILED: convert_png_dry_run stopped with RuntimeError: something unexpected', out)
        self.assertIn('these steps were not run: sync_timestamps', out)
        counted = {(row[1], row[3]): row[4]
                   for row in self.workbook()[organize.COUNTS_SHEET].iter_rows(min_row=2, values_only=True)}
        self.assertEqual(counted.get(('fill_blanks', 'already-dated')), 2, counted)
        self.assertEqual(counted.get(('convert_png', 'step-failed')), 1, counted)
        self.assertFalse(any(phase == 'sync_timestamps' for phase, _ in counted), counted)

    def test_no_later_step_runs(self):
        with mock.patch.object(organize, 'convert_pngs', side_effect=self.crash), \
                mock.patch.object(organize, 'sync_timestamps') as sync:
            run(self.root, '--all', '--apply')

        sync.assert_not_called()

    def test_a_single_step_that_stops_is_still_recorded(self):
        with mock.patch.object(organize, 'sync_timestamps', side_effect=self.crash):
            code, out = run(self.root, '--sync-timestamps')

        self.assertEqual(code, 1, out)
        self.assertNotIn('were not run', out)
        self.assertIn('Run log', self.workbook().sheetnames)


if __name__ == '__main__':
    unittest.main()
