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

    def test_moves_junk_straight_into_junk_and_deletes_nothing(self):
        self.build()
        code, out = run(self.root, '--move-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.day), ['img_1.jpg'])
        junk = self.root / '_junk'
        self.assertEqual(names(junk), ['._img_1.jpg', 'img_1.aae', 'thumbs.db'])
        self.assertEqual((junk / 'IMG_1.AAE').read_text(), '<plist/>')
        self.assertIn('MOVED (AAE): ', out)

    def test_old_delete_junk_flag_moves_too(self):
        self.build()
        code, out = run(self.root, '--delete-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('img_1.aae', names(self.root / '_junk'))
        self.assertNotIn('DELETED', out)

    def test_a_name_taken_in_junk_gets_its_subfolder_name(self):
        self.build()
        old = self.root / '_junk' / 'IMG_1.AAE'
        old.parent.mkdir(parents=True)
        old.write_text('kept from last time')

        code, out = run(self.root, '--move-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(old.read_text(), 'kept from last time')
        self.assertEqual((self.root / '_junk' / 'IMG_1_Trip.AAE').read_text(), '<plist/>')
        self.assertNotIn('img_1.aae', names(self.day))

    def test_never_overwrites_a_file_already_in_junk(self):
        self.build()
        junk = self.root / '_junk'
        junk.mkdir()
        for name in ('IMG_1.AAE', 'IMG_1_Trip.AAE'):
            (junk / name).write_text('kept from last time')

        code, out = run(self.root, '--move-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('COLLISION, skipping', out)
        for name in ('IMG_1.AAE', 'IMG_1_Trip.AAE'):
            self.assertEqual((junk / name).read_text(), 'kept from last time')
        self.assertIn('img_1.aae', names(self.day))

    def test_every_folders_thumbnail_cache_gets_its_own_name(self):
        for day in ('2020-01-01', '2020-01-02'):
            (self.root / day).mkdir(parents=True)
            (self.root / day / 'Thumbs.db').write_bytes(b'cache')

        code, out = run(self.root, '--move-junk')
        self.assertEqual(code, 0, out)
        # The dry run already tells the two apart
        self.assertIn('-> _junk' + os.sep + 'Thumbs.db', out)
        self.assertIn('-> _junk' + os.sep + 'Thumbs_2020-01-02.db', out)

        code, out = run(self.root, '--move-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_junk'), ['thumbs.db', 'thumbs_2020-01-02.db'])

    def test_undated_files_set_aside_keep_their_folders_date(self):
        # US-46
        ad = '0c4cda27-b4cc-4e92-a446-d6b780f24a64'
        for day in ('2020-01-01', '2020-01-02'):
            (self.root / 'Trip' / day).mkdir(parents=True)
            (self.root / 'Trip' / day / 'clip.mp4').write_bytes(b'')
        make_image(self.root / 'Trip' / '2020-01-01' / f'{ad}.jpg')
        # The nearest dated folder above counts, however deep the file is
        make_image(self.root / 'Trip' / '2020-01-02' / 'Phone' / f'{ad}.jpg')
        # A dated ad, a name holding a date and an ad with no dated folder keep their names
        dated = '54ac2fda0a6755305200011c-b30-600.jpg'
        make_image(self.root / 'Trip' / '2020-01-01' / dated, taken=datetime.datetime(2019, 5, 5, 9, 0, 0))
        named = '492887-1648448524975-3d62u_2023-02-26.webp'
        make_image(self.root / 'Trip' / '2020-01-01' / named, fmt='WEBP')
        loose = '55d58970f6cd4574f635d6e3_568-1443241239.jpg'
        make_image(self.root / 'Trip' / loose)

        code, out = run(self.root, '--move-incomplete', '--quarantine-ads')
        self.assertEqual(code, 0, out)
        self.assertIn('-> _incomplete' + os.sep + 'clip_2020-01-01.mp4', out)

        code, out = run(self.root, '--move-incomplete', '--quarantine-ads', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_incomplete'), ['clip_2020-01-01.mp4', 'clip_2020-01-02.mp4'])
        self.assertEqual(names(self.root / '_ads'), sorted(
            [f'{ad}_2020-01-01.jpg', f'{ad}_2020-01-02.jpg', dated, named, loose]))

    def test_an_undated_name_taken_with_its_date_is_a_collision(self):
        for trip in ('Beach', 'Lake'):
            (self.root / trip / '2020-01-01').mkdir(parents=True)
            (self.root / trip / '2020-01-01' / 'clip.mp4').write_bytes(b'')

        code, out = run(self.root, '--move-incomplete', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('COLLISION, skipping', out)
        self.assertEqual(names(self.root / '_incomplete'), ['clip_2020-01-01.mp4'])
        self.assertEqual(names(self.root / 'Lake' / '2020-01-01'), ['clip.mp4'])

    def test_a_read_only_thumbnail_cache_is_moved(self):
        self.build()
        os.chmod(self.day / 'Thumbs.db', 0o444)
        code, out = run(self.root, '--move-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('thumbs.db', names(self.root / '_junk'))

    def test_flatten_moves_orphan_sony_sidecars_into_junk(self):
        sub = self.root / '2014-07-17'
        sub.mkdir(parents=True)
        (sub / 'gone.MTS.modd').write_bytes(b'index')

        code, out = run(self.root, '--flatten', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_junk'), ['gone.mts.modd'])
        self.assertIn('"orphan-sidecars-moved": 1', out)

    def test_final_check_reports_what_is_in_junk(self):
        # Junk is set aside inside a year folder; the final check is given
        # the folder that holds the year folders
        self.build()
        run(self.root / '2020-01-01', '--move-junk', '--apply')
        code, out = run(self.root, '--final-check')
        self.assertEqual(code, 0, out)
        self.assertIn('IN JUNK: 2020-01-01/_junk (3 file(s))', out)
        self.assertIn('2020-01-01: 0 in _ads, 0 in _incomplete, 3 in _junk, 0 video(s)', out)


def make_thumbnail(path, size=(384, 512), camera=None):
    """Write a JPEG the size of a phone gallery thumbnail, optionally with a
    camera Make tag."""
    from PIL import Image
    img = Image.new('RGB', size, (40, 120, 200))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    exif = Image.Exif()
    if camera:
        exif[0x010F] = camera
    img.save(path, 'JPEG', exif=exif)


class PhoneThumbnailTests(unittest.TestCase):
    """BUG-33: a phone's gallery thumbnails, imported loose in a dated folder,
    were given the folder's date and flattened in among the photos. BUG-34:
    they are set aside only by the optional --move-thumbnails, once dated."""

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.day = self.root / '2026-11-02'

    def test_recognises_a_thumbnail_by_name_size_and_missing_camera(self):
        make_thumbnail(self.day / '46.jpg')
        make_thumbnail(self.day / '47 (2).jpg', size=(270, 585))
        self.assertTrue(organize.is_phone_thumbnail(str(self.day / '46.jpg')))
        self.assertTrue(organize.is_phone_thumbnail(str(self.day / '47 (2).jpg')))

    def test_keeps_photos_that_only_look_like_one(self):
        make_thumbnail(self.day / '48.jpg', camera='samsung')        # camera info
        make_thumbnail(self.day / '49.jpg', size=(3000, 4000))       # full size
        make_thumbnail(self.day / 'IMG_50.jpg')                      # not a bare number
        make_thumbnail(self.day / '51.png')                          # not named JPEG
        (self.day / '52.jpg').write_text('not a picture')
        for name in ('48.jpg', '49.jpg', 'IMG_50.jpg', '51.png', '52.jpg'):
            self.assertFalse(organize.is_phone_thumbnail(str(self.day / name)), name)

    def date(self, path, when='2026:11:02 12:00:00'):
        """Give a thumbnail a Date Taken, as --fill-blanks would."""
        organize._write_exif_date_image(str(path), datetime.datetime.strptime(when, '%Y:%m:%d %H:%M:%S'))

    def test_move_junk_leaves_thumbnails_where_they_are(self):
        """BUG-34: --move-junk runs before dates are written, so it must not
        take a thumbnail out of its dated folder."""
        make_thumbnail(self.day / '46.jpg')
        (self.day / 'Thumbs.db').write_bytes(b'cache')
        code, out = run(self.root, '--move-junk', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.day), ['46.jpg'])
        self.assertEqual(names(self.root / '_junk'), ['thumbs.db'])
        self.assertFalse((self.root / '_thumbnails').exists())

    def test_move_thumbnails_sets_dated_thumbnails_aside_and_deletes_nothing(self):
        make_thumbnail(self.day / '46.jpg')
        self.date(self.day / '46.jpg')
        make_thumbnail(self.day / '48.jpg', camera='samsung')
        self.date(self.day / '48.jpg')
        before = snapshot(self.root)

        code, out = run(self.root, '--move-thumbnails')
        self.assertEqual(code, 0, out)
        self.assertEqual(snapshot(self.root), before, 'a dry run must not move anything')
        self.assertIn('WOULD MOVE (phone thumbnail): ' + os.path.join('2026-11-02', '46.jpg'), out)

        code, out = run(self.root, '--move-thumbnails', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_thumbnails'), ['46.jpg'])
        self.assertEqual(names(self.day), ['48.jpg'])
        self.assertIn('"moved-phone-thumbnails": 1', out)

    def test_move_thumbnails_leaves_an_undated_thumbnail_and_says_why(self):
        make_thumbnail(self.day / '46.jpg')
        code, out = run(self.root, '--move-thumbnails', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.day), ['46.jpg'])
        self.assertIn('LEFT (no Date Taken yet; run --fill-blanks first): ' + os.path.join('2026-11-02', '46.jpg'), out)
        self.assertIn('"left-undated": 1', out)

    def test_a_thumbnail_name_taken_gets_its_subfolder_name(self):
        for day in ('2026-11-02', '2026-11-03'):
            make_thumbnail(self.root / day / '46.jpg')
            self.date(self.root / day / '46.jpg')
        code, out = run(self.root, '--move-thumbnails', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_thumbnails'), ['46.jpg', '46_2026-11-03.jpg'])

    def test_all_leaves_thumbnails_alone_and_dates_them(self):
        make_thumbnail(self.day / '46.jpg')
        code, out = run(self.root, '--all', '--apply')
        self.assertEqual(code, 0, out)
        self.assertFalse((self.root / '_thumbnails').exists(), '--all must not move thumbnails')
        dt = organize.read_metadata(str(self.day / '46.jpg'), '.jpg')['date_taken']
        self.assertEqual(dt, datetime.datetime(2026, 11, 2, 12, 0))

    def test_all_with_move_thumbnails_moves_them_after_they_get_the_folders_date(self):
        make_thumbnail(self.day / '46.jpg')
        code, out = run(self.root, '--all', '--move-thumbnails', '--flatten', '--apply')
        self.assertEqual(code, 0, out)
        moved = self.root / '_thumbnails' / '46.jpg'
        self.assertTrue(moved.exists(), out)
        self.assertEqual(organize.read_metadata(str(moved), '.jpg')['date_taken'], datetime.datetime(2026, 11, 2, 12, 0))
        self.assertFalse((self.root / '46.jpg').exists(), 'the thumbnail must not be flattened into root')

    def test_other_phases_and_flatten_leave_the_thumbnails_folder_alone(self):
        make_thumbnail(self.root / '_thumbnails' / 'sub' / '46.jpg')
        code, out = run(self.root, '--all', '--flatten', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_thumbnails' / 'sub'), ['46.jpg'])

    def test_final_check_reports_what_is_in_thumbnails(self):
        make_thumbnail(self.day / '46.jpg')
        make_thumbnail(self.day / '47.jpg')
        self.date(self.day / '46.jpg')
        self.date(self.day / '47.jpg')
        run(self.day, '--move-thumbnails', '--apply')
        code, out = run(self.root, '--final-check')
        self.assertEqual(code, 0, out)
        self.assertIn('IN THUMBNAILS: 2026-11-02/_thumbnails (2 file(s))', out)
        self.assertIn('2026-11-02: 0 in _ads, 0 in _incomplete, 0 in _junk, 2 in _thumbnails, ', out)
        self.assertIn('"thumbnail-files": 2', out)


if __name__ == '__main__':
    unittest.main()
