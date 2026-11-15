"""WebP pictures become dated JPEGs, and the WebP moves into _converted
once the JPEG is confirmed to be the same picture (US-57).
Run with: py -m unittest discover tests -v"""

import datetime
import os
import pathlib
import shutil
import tempfile
import unittest

from PIL import Image

from test_dry_run import snapshot
from test_smoke import date_taken, make_image, names, organize, run


def make_animated(path):
    frames = [Image.new('RGB', (64, 48), c) for c in ((200, 30, 30), (30, 200, 30))]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    frames[0].save(path, 'WEBP', save_all=True, append_images=frames[1:], duration=100)


def make_transparent(path):
    img = Image.new('RGBA', (64, 48), (200, 30, 30, 255))
    img.putpixel((0, 0), (0, 0, 0, 0))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, 'WEBP', lossless=True)


class ConvertWebpTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.day = self.root / 'Temp' / '2022-05-08'
        self.converted = self.root / '_converted'

    def test_preview_lists_the_conversion_and_the_move_and_changes_nothing(self):
        make_image(self.day / 'IMG_20220508_185526_425.webp', fmt='WEBP')
        before = snapshot(self.root)
        code, out = run(self.root, '--convert-webp')
        self.assertEqual(code, 0, out)
        rel = os.path.join('Temp', '2022-05-08', 'IMG_20220508_185526_425.webp')
        self.assertIn(f'WOULD CONVERT: {rel} -> IMG_20220508_185526_425.jpg '
                      '(Date Taken 2022-05-08 18:55:26 from filename)', out)
        self.assertIn(f'WOULD MOVE (converted to IMG_20220508_185526_425.jpg): {rel} -> '
                      + os.path.join('_converted', 'IMG_20220508_185526_425.webp'), out)
        self.assertEqual(snapshot(self.root), before)

    def test_apply_writes_a_dated_jpeg_and_sets_the_webp_aside(self):
        make_image(self.day / 'IMG_20220508_185526_425.webp', fmt='WEBP')
        code, out = run(self.root, '--convert-webp', '--apply')
        self.assertEqual(code, 0, out)
        jpg = self.day / 'IMG_20220508_185526_425.jpg'
        self.assertEqual(date_taken(jpg), datetime.datetime(2022, 5, 8, 18, 55, 26))
        with Image.open(jpg) as img:
            self.assertEqual((img.format, img.size), ('JPEG', (64, 48)))
        # Moved aside, not deleted
        self.assertEqual(names(self.day), ['img_20220508_185526_425.jpg'])
        self.assertEqual(names(self.converted), ['img_20220508_185526_425.webp'])

    def test_a_webp_with_no_date_in_its_name_gets_the_folders_date(self):
        make_image(self.day / 'saved.webp', fmt='WEBP')
        _, out = run(self.root, '--convert-webp', '--apply')
        self.assertIn('(Date Taken 2022-05-08 12:00:00 from folder)', out)
        self.assertEqual(date_taken(self.day / 'saved.jpg'), datetime.datetime(2022, 5, 8, 12, 0, 0))

    def test_a_webps_own_date_taken_is_kept(self):
        taken = datetime.datetime(2021, 1, 2, 3, 4, 5)
        make_image(self.day / 'IMG_20220508_185526_425.webp', fmt='WEBP', taken=taken)
        _, out = run(self.root, '--convert-webp', '--apply')
        self.assertIn('(Date Taken 2021-01-02 03:04:05 kept)', out)
        self.assertEqual(date_taken(self.day / 'IMG_20220508_185526_425.jpg'), taken)

    def test_a_webp_with_no_date_anywhere_is_still_converted(self):
        make_image(self.root / 'Saved' / 'sticker.webp', fmt='WEBP')
        code, out = run(self.root, '--convert-webp', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIsNone(date_taken(self.root / 'Saved' / 'sticker.jpg'))
        self.assertEqual(names(self.converted), ['sticker.webp'])

    def test_animated_and_transparent_webps_stay_webp(self):
        make_animated(self.day / 'moving.webp')
        make_transparent(self.day / 'sticker.webp')
        code, out = run(self.root, '--convert-webp', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('SKIPPED (animated, stays WEBP): ' + os.path.join('Temp', '2022-05-08', 'moving.webp'), out)
        self.assertIn('SKIPPED (has transparent pixels, stays WEBP): '
                      + os.path.join('Temp', '2022-05-08', 'sticker.webp'), out)
        self.assertEqual(names(self.day), ['moving.webp', 'sticker.webp'])
        self.assertFalse(self.converted.exists())

    def test_a_webp_that_is_really_another_format_is_left_alone(self):
        make_image(self.day / 'fake.webp', fmt='PNG')
        _, out = run(self.root, '--convert-webp', '--apply')
        self.assertIn('NOT A WEBP (really .png, left alone)', out)
        self.assertEqual(names(self.day), ['fake.webp'])

    def test_a_jpeg_already_holding_the_name_is_never_overwritten(self):
        make_image(self.day / 'photo.webp', fmt='WEBP')
        make_image(self.day / 'photo.jpg', color=(10, 200, 10), fmt='JPEG')
        before = snapshot(self.root)
        _, out = run(self.root, '--convert-webp', '--apply')
        self.assertIn('SKIPPED (photo.jpg already exists): ' + os.path.join('Temp', '2022-05-08', 'photo.webp'), out)
        self.assertEqual(snapshot(self.root), before)

    def test_a_name_already_in_converted_gets_its_folder_name(self):
        make_image(self.day / 'saved.webp', fmt='WEBP')
        make_image(self.root / 'Temp' / '2022-05-09' / 'saved.webp', fmt='WEBP')
        _, out = run(self.root, '--convert-webp', '--apply')
        self.assertEqual(names(self.converted), ['saved.webp', 'saved_2022-05-09.webp'])

    def test_a_second_run_finds_nothing_to_do(self):
        make_image(self.day / 'saved.webp', fmt='WEBP')
        run(self.root, '--convert-webp', '--apply')
        before = snapshot(self.root)
        _, out = run(self.root, '--convert-webp', '--apply')
        self.assertNotIn('CONVERTED', out)
        self.assertEqual(snapshot(self.root), before)

    def test_same_picture_check(self):
        make_image(self.day / 'a.webp', fmt='WEBP')
        make_image(self.day / 'a.jpg', fmt='JPEG')
        make_image(self.day / 'green.jpg', color=(10, 200, 10), fmt='JPEG')
        Image.new('RGB', (32, 32)).save(self.day / 'small.jpg')
        self.assertIsNone(organize._same_picture(str(self.day / 'a.webp'), str(self.day / 'a.jpg')))
        self.assertIn('pixel difference', organize._same_picture(str(self.day / 'a.webp'), str(self.day / 'green.jpg')))
        self.assertEqual(organize._same_picture(str(self.day / 'a.webp'), str(self.day / 'small.jpg')),
                         'sizes differ, 64x48 vs 32x32')

    def test_fill_blanks_points_at_convert_webp(self):
        make_image(self.day / 'saved.webp', fmt='WEBP')
        _, out = run(self.root, '--fill-blanks')
        self.assertIn('--convert-webp turns them into dated JPEGs', out)

    def test_convert_webp_is_not_part_of_all_and_runs_before_fill_blanks(self):
        self.assertNotIn('convert_webp', organize.ALL_PHASES)
        order = organize.PHASE_ORDER
        self.assertLess(order.index('convert_webp'), order.index('fill_blanks'))

    def test_other_steps_leave_converted_alone_and_the_final_check_counts_it(self):
        make_image(self.converted / 'IMG_20220508_185526_425.webp', fmt='WEBP')
        before = snapshot(self.converted)
        run(self.root, '--fill-blanks', '--convert-webp', '--flatten', '--apply')
        self.assertEqual(snapshot(self.converted), before)
        _, out = run(self.root, '--final-check')
        self.assertIn('IN CONVERTED: _converted (1 file(s))', out)
        self.assertIn('1 in _converted, ', out)


if __name__ == '__main__':
    unittest.main()
