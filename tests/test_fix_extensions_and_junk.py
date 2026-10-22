"""--fix-extensions renames misnamed photos and videos and is part of --all
(US-04, US-19), and junk is moved into _junk rather than deleted (US-14,
US-21). Run with: py -m unittest discover tests -v"""

import datetime
import os
import pathlib
import shutil
import tempfile
import unittest

from test_dry_run import snapshot
from test_smoke import make_image, names, organize, run


class FixExtensionsTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.day = self.root / '2020-01-01'

    def test_previews_then_renames_keeping_the_extension_case(self):
        make_image(self.day / 'IMG_1.PNG', fmt='JPEG')
        make_image(self.day / 'shot.gif', fmt='PNG')
        make_image(self.day / 'right.jpeg')
        before = snapshot(self.root)

        code, out = run(self.root, '--fix-extensions')
        self.assertEqual(code, 0, out)
        self.assertEqual(snapshot(self.root), before, 'a dry run must not rename anything')
        self.assertIn('WOULD RENAME: ' + os.path.join('2020-01-01', 'IMG_1.PNG') + ' -> IMG_1.JPG (really JPG)', out)

        code, out = run(self.root, '--fix-extensions', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(os.listdir(self.day)), ['IMG_1.JPG', 'right.jpeg', 'shot.png'])
        self.assertIn('"correct": 1', out)

    def test_a_taken_name_is_a_collision_and_both_files_stay(self):
        make_image(self.day / 'IMG_2.PNG', fmt='JPEG')
        make_image(self.day / 'IMG_2.JPG', color=(10, 200, 10))

        code, out = run(self.root, '--fix-extensions', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('COLLISION, not renaming', out)
        self.assertEqual(names(self.day), ['img_2.jpg', 'img_2.png'])

    def test_two_files_claiming_one_name_rename_only_the_first(self):
        make_image(self.day / 'IMG_3.GIF', fmt='JPEG')
        make_image(self.day / 'IMG_3.PNG', fmt='JPEG')

        code, out = run(self.root, '--fix-extensions')
        self.assertEqual(out.count('WOULD RENAME'), 1, out)
        self.assertIn('COLLISION, not renaming', out)

    def test_leaves_alone_what_it_cannot_be_sure_of(self):
        (self.day).mkdir(parents=True)
        (self.day / 'empty.jpg').write_bytes(b'')
        (self.day / 'IMG_E1.JPG').write_text('<?xml version="1.0"?><plist version="1.0"></plist>')
        (self.day / 'burst.heic').write_bytes(b'\x00\x00\x00\x18ftyphevc' + b'\x00' * 40)
        (self.day / 'song.m4a').write_bytes(b'\x00\x00\x00\x18ftypM4A ' + b'\x00' * 40)
        make_image(self.day / 'notes.txt', fmt='JPEG')
        before = snapshot(self.root)

        code, out = run(self.root, '--fix-extensions', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(snapshot(self.root), before, out)
        self.assertIn('EMPTY (0 bytes', out)
        self.assertIn('NOT MEDIA (plist', out)
        self.assertIn('UNKNOWN FORMAT (left alone): ' + os.path.join('2020-01-01', 'burst.heic'), out)

    def test_knows_the_older_video_formats(self):
        self.day.mkdir(parents=True)
        (self.day / 'clip.mp4').write_bytes(b'RIFF\x00\x00\x00\x00AVI LIST' + b'\x00' * 40)
        (self.day / 'tape.mov').write_bytes(b'\x00\x00\x01\xba' + b'\x00' * 40)
        (self.day / 'old.avi').write_bytes(b'\x30\x26\xb2\x75\x8e\x66\xcf\x11' + b'\x00' * 40)

        code, out = run(self.root, '--fix-extensions', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.day), ['clip.avi', 'old.wmv', 'tape.mpg'])

    def test_holding_folders_are_left_alone(self):
        make_image(self.root / '_ads' / 'ad.png', fmt='JPEG')
        make_image(self.root / '_junk' / 'x.png', fmt='JPEG')

        code, out = run(self.root, '--fix-extensions', '--apply')
        self.assertEqual(names(self.root / '_ads'), ['ad.png'])
        self.assertEqual(names(self.root / '_junk'), ['x.png'])

    def test_all_fixes_extensions_first_so_the_photo_gets_its_date(self):
        # A JPEG named .PNG: once renamed, --fill-blanks writes its date and
        # --convert-png leaves it alone
        make_image(self.day / 'IMG_20200101_090000.PNG', fmt='JPEG')
        self.assertEqual(organize.ALL_PHASES[0], 'fix_extensions')

        code, out = run(self.root, '--all', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.day), ['img_20200101_090000.jpg'])
        taken = organize.read_metadata(str(self.day / 'IMG_20200101_090000.JPG'), '.jpg')['date_taken']
        self.assertEqual(taken, datetime.datetime(2020, 1, 1, 9, 0, 0))


class MoveJunkTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.day = self.root / '2020-01-01' / 'Trip'

    def build(self):
        make_image(self.day / 'IMG_1.JPG')
        (self.day / 'IMG_1.AAE').write_text('<plist/>')
        (self.day / 'Thumbs.db').write_bytes(b'\0cache')
        (self.day / '._IMG_1.JPG').write_bytes(organize.APPLEDOUBLE_MAGIC + b'\x00' * 60)

    def test_moves_junk_into_junk_keeping_its_path_and_deletes_nothing(self):
        self.build()
        code, out = run(self.root, '--move-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.day), ['img_1.jpg'])
        junk = self.root / '_junk' / '2020-01-01' / 'Trip'
        self.assertEqual(names(junk), ['._img_1.jpg', 'img_1.aae', 'thumbs.db'])
        self.assertEqual((junk / 'IMG_1.AAE').read_text(), '<plist/>')
        self.assertIn('MOVED (AAE): ', out)

    def test_old_delete_junk_flag_moves_too(self):
        self.build()
        code, out = run(self.root, '--delete-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('img_1.aae', names(self.root / '_junk' / '2020-01-01' / 'Trip'))
        self.assertNotIn('DELETED', out)

    def test_never_overwrites_a_file_already_in_junk(self):
        self.build()
        old = self.root / '_junk' / '2020-01-01' / 'Trip' / 'IMG_1.AAE'
        old.parent.mkdir(parents=True)
        old.write_text('kept from last time')

        code, out = run(self.root, '--move-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('COLLISION, skipping', out)
        self.assertEqual(old.read_text(), 'kept from last time')
        self.assertIn('img_1.aae', names(self.day))

    def test_a_read_only_thumbnail_cache_is_moved(self):
        self.build()
        os.chmod(self.day / 'Thumbs.db', 0o444)
        code, out = run(self.root, '--move-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('thumbs.db', names(self.root / '_junk' / '2020-01-01' / 'Trip'))

    def test_flatten_moves_orphan_sony_sidecars_into_junk(self):
        sub = self.root / '2014-07-17'
        sub.mkdir(parents=True)
        (sub / 'gone.MTS.modd').write_bytes(b'index')

        code, out = run(self.root, '--flatten', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_junk' / '2014-07-17'), ['gone.mts.modd'])
        self.assertIn('"orphan-sidecars-moved": 1', out)

    def test_final_check_reports_what_is_in_junk(self):
        # Junk is set aside inside a year folder; the final check is given
        # the folder that holds the year folders
        self.build()
        run(self.root / '2020-01-01', '--move-junk', '--apply')
        code, out = run(self.root, '--final-check')
        self.assertEqual(code, 0, out)
        self.assertIn('IN JUNK: 2020-01-01/_junk (3 file(s))', out)
        self.assertIn('2020-01-01: 0 in _ads, 0 in _incomplete, 3 in _junk', out)


if __name__ == '__main__':
    unittest.main()
