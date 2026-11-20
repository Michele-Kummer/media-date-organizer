"""Optional sorting of pictures into groups (US-60): screenshots into
_screenshots (--move-screenshots), backup thumbnails into _thumbnails
(--move-thumbnails), or both at once (--sort-pictures). Nothing is deleted.
Run with: py -m unittest discover tests -v"""

import datetime
import os
import pathlib
import shutil
import tempfile
import unittest

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from test_dry_run import snapshot
from test_smoke import names, organize, run

TAKEN = datetime.datetime(2023, 12, 20, 12, 0, 0)

IOS_XMP = ('<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
           '<rdf:Description xmlns:exif="http://ns.adobe.com/exif/1.0/"><exif:UserComment><rdf:Alt>'
           '<rdf:li xml:lang="x-default">Screenshot</rdf:li></rdf:Alt></exif:UserComment>'
           '</rdf:Description></rdf:RDF></x:xmpmeta>')


def make_picture(path, size=(1170, 2532), fmt=None, camera=None, taken=TAKEN, xmp=None, comment=None):
    """Write a picture the size of a phone screen, optionally with a camera
    Make, a Date Taken, an XMP packet (PNG) or an EXIF UserComment (JPEG)."""
    path = pathlib.Path(path)
    os.makedirs(path.parent, exist_ok=True)
    img = Image.new('RGB', size, (40, 120, 200))
    fmt = fmt or {'.png': 'PNG'}.get(path.suffix.lower(), 'JPEG')
    exif = Image.Exif()
    if camera:
        exif[0x010F] = camera
    if comment is not None:
        exif.get_ifd(0x8769)[0x9286] = comment
    if fmt == 'PNG':
        info = PngInfo()
        if xmp:
            info.add_itxt('XML:com.adobe.xmp', xmp)
        img.save(path, 'PNG', pnginfo=info, exif=exif)
    else:
        img.save(path, fmt, exif=exif)
    if taken is not None:
        organize._write_exif_date_image(str(path), taken)


def make_thumbnail(path, size=(256, 256), **kw):
    make_picture(path, size=size, **kw)


class ScreenshotRecognitionTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_recognises_screenshot_names_from_phones_and_computers(self):
        for name in ('Screenshot_20231220-142355.png',                  # Android, Pixel
                     'Screenshot_20231220_142355_Chrome.jpg',           # Samsung
                     'Screenshot_2023-12-20-14-23-55-123_com.app.jpg',  # Xiaomi
                     'Screenshot (12).png',                             # Windows
                     'Screenshot 2023-12-20 142355.png',                # Snipping Tool
                     'Screen Shot 2023-12-20 at 2.23.55 PM.png',        # older macOS
                     'Screenshot 2023-12-20 at 14.23.55.png',           # macOS
                     'Screenshot from 2023-12-20 14-23-55.png',         # GNOME
                     'screencap-20231220.png', 'Screen Capture 1.jpg', 'ScreenClip.png',
                     'Bildschirmfoto 2023-12-20 um 14.23.55.png', "Capture d'écran 2023-12-20.png",
                     'Captura de pantalla 2023-12-20.png', 'Schermata 2023-12-20.png',
                     'Skärmavbild 2023-12-20.png', 'スクリーンショット 2023-12-20.png'):
            with self.subTest(name=name):
                make_picture(self.root / name)
                self.assertEqual(organize.screenshot_reason(str(self.root / name)), 'name')

    def test_recognises_an_iphone_screenshot_by_its_tag(self):
        make_picture(self.root / 'IMG_1234.PNG', xmp=IOS_XMP)
        make_picture(self.root / 'IMG_1235.JPG', comment=b'ASCII\x00\x00\x00Screenshot')
        self.assertEqual(organize.screenshot_reason(str(self.root / 'IMG_1234.PNG')), 'tag')
        self.assertEqual(organize.screenshot_reason(str(self.root / 'IMG_1235.JPG')), 'tag')

    def test_keeps_pictures_that_only_look_like_one(self):
        make_picture(self.root / 'Screenshot_20231220-142355.jpg', camera='samsung')   # camera info
        make_picture(self.root / 'IMG_1234.PNG')                                       # no tag
        make_picture(self.root / 'Screenshotting the sunset.jpg')                      # a longer word
        make_picture(self.root / 'Screens.png')
        make_picture(self.root / 'My screenshot.png')                                  # not at the start
        make_picture(self.root / 'IMG_1236.JPG', comment=b'ASCII\x00\x00\x00Holiday')  # another comment
        make_picture(self.root / 'Screenshot_1.gif', fmt='GIF')                        # not PNG, JPEG or HEIC
        for name in ('Screenshot_20231220-142355.jpg', 'IMG_1234.PNG', 'Screenshotting the sunset.jpg',
                     'Screens.png', 'My screenshot.png', 'IMG_1236.JPG', 'Screenshot_1.gif'):
            with self.subTest(name=name):
                self.assertIsNone(organize.screenshot_reason(str(self.root / name)))


class MoveScreenshotsTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.day = self.root / '2023-12-20'

    def test_previews_then_moves_screenshots_and_deletes_nothing(self):
        make_picture(self.day / 'Screenshot_20231220-142355.png')
        make_picture(self.day / 'IMG_1234.PNG', xmp=IOS_XMP)
        make_picture(self.day / 'IMG_1240.JPG', camera='Apple')
        before = snapshot(self.root)

        code, out = run(self.root, '--move-screenshots')
        self.assertEqual(code, 0, out)
        self.assertEqual(snapshot(self.root), before, 'a dry run must not move anything')
        self.assertIn('WOULD MOVE (screenshot, by name): '
                      + os.path.join('2023-12-20', 'Screenshot_20231220-142355.png'), out)
        self.assertIn('WOULD MOVE (screenshot, by tag): ' + os.path.join('2023-12-20', 'IMG_1234.PNG'), out)

        code, out = run(self.root, '--move-screenshots', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_screenshots'), ['img_1234.png', 'screenshot_20231220-142355.png'])
        self.assertEqual(names(self.day), ['img_1240.jpg'])
        self.assertIn('"moved-screenshots": 2', out)

    def test_leaves_an_undated_screenshot_and_says_why(self):
        make_picture(self.day / 'Screenshot (12).png', taken=None)
        code, out = run(self.root, '--move-screenshots', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.day), ['screenshot (12).png'])
        self.assertIn('LEFT (no Date Taken yet; run --fill-blanks first): '
                      + os.path.join('2023-12-20', 'Screenshot (12).png'), out)
        self.assertIn('"left-undated": 1', out)

    def test_a_taken_name_gets_its_subfolder_name(self):
        for day in ('2023-12-20', '2023-12-21'):
            make_picture(self.root / day / 'Screenshot (1).png')
        code, out = run(self.root, '--move-screenshots', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_screenshots'), ['screenshot (1).png', 'screenshot (1)_2023-12-21.png'])

    def test_all_leaves_screenshots_alone_and_dates_them(self):
        make_picture(self.day / 'Screenshot (12).jpg', taken=None)
        code, out = run(self.root, '--all', '--apply')
        self.assertEqual(code, 0, out)
        self.assertFalse((self.root / '_screenshots').exists(), '--all must not move screenshots')

    def test_all_with_move_screenshots_moves_them_after_they_get_the_folders_date(self):
        make_picture(self.day / 'Screenshot (12).jpg', taken=None)
        code, out = run(self.root, '--all', '--move-screenshots', '--flatten', '--apply')
        self.assertEqual(code, 0, out)
        moved = self.root / '_screenshots' / 'Screenshot (12).jpg'
        self.assertTrue(moved.exists(), out)
        self.assertEqual(organize.read_metadata(str(moved), '.jpg')['date_taken'], datetime.datetime(2023, 12, 20, 12, 0))

    def test_other_phases_and_flatten_leave_the_screenshots_folder_alone(self):
        make_picture(self.root / '_screenshots' / '2023-12-20' / 'Screenshot (12).jpg')
        code, out = run(self.root, '--all', '--sort-pictures', '--flatten', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_screenshots' / '2023-12-20'), ['screenshot (12).jpg'])

    def test_final_check_reports_what_is_in_screenshots(self):
        make_picture(self.day / 'Screenshot (12).png')
        run(self.day, '--move-screenshots', '--apply')
        code, out = run(self.root, '--final-check')
        self.assertEqual(code, 0, out)
        self.assertIn('IN SCREENSHOTS: 2023-12-20/_screenshots (1 file(s))', out)
        self.assertIn('2023-12-20: 0 in _ads, 0 in _incomplete, 0 in _junk, 1 in _screenshots, ', out)
        self.assertIn('"screenshot-files": 1', out)
        self.assertNotIn('INCOMPLETE', out)


class BackupThumbnailTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.day = self.root / '2023-12-20'

    def kind(self, rel):
        return organize.thumbnail_kind(str(self.root / rel), str(self.root))

    def test_recognises_backup_thumbnails_by_name_and_folder(self):
        for rel in ('2023-12-20/IMG_1234_thumb.jpg', '2023-12-20/thumb_IMG_1234.jpg',
                    '2023-12-20/IMG_1234.thumb.jpg', '2023-12-20/IMG_1234-thumbnail.png',
                    '2023-12-20/tn_IMG_1234.jpg', '2023-12-20/IMG_1234_thumb (2).jpg',
                    'DCIM/.thumbnails/abc.jpg', 'Backup/Thumbs/IMG_1.png'):
            with self.subTest(rel=rel):
                make_thumbnail(self.root / rel)
                self.assertEqual(self.kind(rel), 'backup')

    def test_phone_gallery_thumbnails_are_still_recognised(self):
        make_thumbnail(self.day / '46.jpg')
        self.assertEqual(self.kind('2023-12-20/46.jpg'), 'phone')

    def test_recognises_thumbnail_cache_files(self):
        for rel in ('iPod Photo Cache/F00/F1019_1.ithmb', 'DCIM/.thumbnails/.thumbdata3--1967290299',
                    'DCIM/.thumbnails/.thumbdata4--1967290299'):
            with self.subTest(rel=rel):
                (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
                (self.root / rel).write_bytes(b'\xff\xd8' + b'\0' * 64)
                self.assertEqual(self.kind(rel), 'cache')

    def test_keeps_photos_that_only_look_like_one(self):
        make_thumbnail(self.day / 'west sucking thumb.jpg')                    # a word, not a marker
        make_thumbnail(self.day / 'thumbtack.jpg')
        make_thumbnail(self.day / 'IMG_1234_thumb.jpg', size=(3000, 4000))     # full size
        make_thumbnail(self.day / 'IMG_1235_thumb.jpg', camera='Apple')        # camera info
        make_thumbnail(self.root / 'Thumbnails' / 'IMG_1236.jpg', size=(3000, 4000))
        make_thumbnail(self.day / 'IMG_1237_thumb.gif', fmt='GIF')
        (self.day / 'thumbdata.txt').write_text('notes')
        for rel in ('2023-12-20/west sucking thumb.jpg', '2023-12-20/thumbtack.jpg', '2023-12-20/IMG_1234_thumb.jpg',
                    '2023-12-20/IMG_1235_thumb.jpg', 'Thumbnails/IMG_1236.jpg', '2023-12-20/IMG_1237_thumb.gif',
                    '2023-12-20/thumbdata.txt'):
            with self.subTest(rel=rel):
                self.assertIsNone(self.kind(rel))

    def test_move_thumbnails_moves_each_kind_and_counts_it(self):
        make_thumbnail(self.day / '46.jpg')
        make_thumbnail(self.day / 'IMG_1234_thumb.jpg')
        make_thumbnail(self.day / 'IMG_1235_thumb.jpg', taken=None)
        cache = self.root / 'iPod Photo Cache' / 'F00' / 'F1019_1.ithmb'
        cache.parent.mkdir(parents=True)
        cache.write_bytes(b'\0' * 64)
        before = snapshot(self.root)

        code, out = run(self.root, '--move-thumbnails')
        self.assertEqual(code, 0, out)
        self.assertEqual(snapshot(self.root), before, 'a dry run must not move anything')
        self.assertIn('WOULD MOVE (backup thumbnail): ' + os.path.join('2023-12-20', 'IMG_1234_thumb.jpg'), out)
        self.assertIn('WOULD MOVE (thumbnail cache file): ' + os.path.join('iPod Photo Cache', 'F00', 'F1019_1.ithmb'), out)

        code, out = run(self.root, '--move-thumbnails', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_thumbnails'), ['46.jpg', 'f1019_1.ithmb', 'img_1234_thumb.jpg'])
        self.assertEqual(names(self.day), ['img_1235_thumb.jpg'], 'an undated thumbnail must stay')
        for key in ('"moved-phone-thumbnails": 1', '"moved-backup-thumbnails": 1', '"moved-thumbnail-caches": 1',
                    '"left-undated": 1'):
            self.assertIn(key, out)


class KeepScreenshotTagTests(unittest.TestCase):
    """BUG-40: writing a date into a PNG, and converting a PNG to JPEG,
    dropped its XMP, and with it the "Screenshot" tag an iPhone writes."""

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.day = self.root / '2023-12-20'

    def test_fill_blanks_keeps_a_pngs_xmp(self):
        make_picture(self.day / 'IMG_1234.PNG', xmp=IOS_XMP, taken=None)
        code, out = run(self.root, '--fill-blanks', '--apply')
        self.assertEqual(code, 0, out)
        png = str(self.day / 'IMG_1234.PNG')
        self.assertEqual(organize.read_metadata(png, '.png')['date_taken'], datetime.datetime(2023, 12, 20, 12, 0))
        self.assertEqual(organize.screenshot_reason(png), 'tag')

    def test_convert_png_carries_the_tag_into_the_jpeg(self):
        make_picture(self.day / 'IMG_1234.PNG', xmp=IOS_XMP, taken=None)
        code, out = run(self.root, '--fill-blanks', '--convert-png', '--apply')
        self.assertEqual(code, 0, out)
        jpg = str(self.day / 'IMG_1234.jpg')
        self.assertTrue(os.path.exists(jpg), out)
        self.assertEqual(organize.screenshot_reason(jpg), 'tag')
        # Writing a date into the JPEG keeps it too
        organize._write_exif_date_image(jpg, TAKEN)
        self.assertEqual(organize.screenshot_reason(jpg), 'tag')


class SortPicturesTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.day = self.root / '2023-12-20'

    def test_sort_pictures_runs_both_steps_and_deletes_nothing(self):
        make_picture(self.day / 'Screenshot_20231220-142355.png')
        make_thumbnail(self.day / 'IMG_1234_thumb.jpg')
        make_picture(self.day / 'IMG_1240.JPG', camera='Apple')
        count = sum(1 for p in self.root.rglob('*') if p.is_file())

        code, out = run(self.root, '--sort-pictures', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(self.root / '_screenshots'), ['screenshot_20231220-142355.png'])
        self.assertEqual(names(self.root / '_thumbnails'), ['img_1234_thumb.jpg'])
        self.assertEqual(names(self.day), ['img_1240.jpg'])
        media = sum(1 for p in self.root.rglob('*') if p.is_file() and p.suffix != '.xlsx')
        self.assertEqual(media, count, 'no file may be deleted')


if __name__ == '__main__':
    unittest.main()
