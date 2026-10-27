"""BMP files become dated JPEGs (US-29), and the game-ad names found in
E:\\Pictures\\2023 are quarantined (US-30).
Run with: py -m unittest discover tests -v"""

import datetime
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from test_dry_run import SCRIPTS, powershell, snapshot
from test_smoke import date_taken, make_image, names, organize, run


class BmpTests(unittest.TestCase):

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.day = self.root / '2021-05-04'

    def test_convert_bmp_previews_then_writes_a_dated_jpeg(self):
        make_image(self.day / 'scan.bmp', fmt='BMP')
        make_image(self.day / 'IMG_20210503_101500.bmp', fmt='BMP')
        before = snapshot(self.root)
        code, out = run(self.root, '--convert-bmp')
        self.assertEqual(code, 0, out)
        self.assertIn('WOULD CONVERT: ' + os.path.join('2021-05-04', 'scan.bmp')
                      + ' -> scan.jpg (Date Taken 2021-05-04 12:00:00 from folder)', out)
        self.assertEqual(snapshot(self.root), before)

        code, out = run(self.root, '--convert-bmp', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(date_taken(self.day / 'scan.jpg'), datetime.datetime(2021, 5, 4, 12, 0, 0))
        self.assertEqual(date_taken(self.day / 'IMG_20210503_101500.jpg'), datetime.datetime(2021, 5, 3, 10, 15, 0))
        # The original stays for Cleanup-Pictures.ps1, and the picture is unchanged
        self.assertIn('scan.bmp', names(self.day))
        with Image.open(self.day / 'scan.jpg') as img:
            self.assertEqual(img.size, (64, 48))

    def test_a_bmp_that_is_really_another_format_is_left_alone(self):
        make_image(self.day / 'fake.bmp', fmt='PNG')
        code, out = run(self.root, '--convert-bmp', '--apply')
        self.assertEqual(code, 0, out)
        self.assertIn('NOT A BMP (really .png, left alone)', out)
        self.assertNotIn('fake.jpg', names(self.day))

    def test_fill_blanks_points_at_convert_bmp(self):
        make_image(self.day / 'scan.bmp', fmt='BMP')
        _, out = run(self.root, '--fill-blanks')
        self.assertIn('--convert-bmp turns them into dated JPEGs', out)

    def test_convert_bmp_is_not_part_of_all(self):
        self.assertNotIn('convert_bmp', organize.ALL_PHASES)

    @unittest.skipUnless(os.name == 'nt' and powershell(), 'needs PowerShell on Windows')
    def test_cleanup_removes_a_converted_bmp_only(self):
        make_image(self.day / 'scan.bmp', fmt='BMP')
        make_image(self.day / 'other.bmp', fmt='BMP')
        run(self.root, '--convert-bmp', '--apply')
        # other.jpg is replaced by a different picture of the same size
        make_image(self.day / 'other.jpg', color=(10, 200, 10), fmt='JPEG')
        r = subprocess.run([powershell(), '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                            str(SCRIPTS / 'Cleanup-Pictures.ps1'), '-Path', str(self.root), '-Apply'],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn('scan.bmp', names(self.day))
        self.assertIn('scan.jpg', names(self.day))
        self.assertIn('other.bmp', names(self.day), 'a BMP whose JPG differs must be kept')

    @unittest.skipUnless(os.name == 'nt' and powershell(), 'needs PowerShell on Windows')
    def test_cleanup_leaves_a_years_own_ads_alone(self):
        # The same pair in a day folder and in 2022/_ads, where
        # --quarantine-ads puts a year's ads when run on the folder above
        day = self.root / '2022' / '2022-02-14'
        ads = self.root / '2022' / '_ads' / 'Temp'
        for folder in (day, ads):
            make_image(folder / 'scan.bmp', fmt='BMP')
            make_image(folder / 'scan.jpg', fmt='JPEG')
        r = subprocess.run([powershell(), '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                            str(SCRIPTS / 'Cleanup-Pictures.ps1'), '-Path', str(self.root), '-Apply'],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn('scan.bmp', names(day))
        self.assertEqual(names(ads), ['scan.bmp', 'scan.jpg'])


class GameAdTests(unittest.TestCase):
    """The names left in E:\\Pictures\\2023's dated folders, with the date
    endings --apply-moves gave them."""

    ADS = ['492887-1648448524975-3d62u_2023-02-26.webp',
           '89413-1663954992992-x1qmi_2023-03-04.webp',
           '__d2duuy9yo5pldo.cloudfront.net_codigames_6e945046-0a56-4291-814d-1cbf498cf2be_2023-02-28.gif',
           'lbay6fy2_fftxeca_itehyhqsmpyyszx7_2023-03-03.gif',
           'lgmzp6d4_qwjiwfv_nan9eutqzjcawect_2023-04-19.gif',
           'icon_2023-11-30.webp', 'draw_title.raw', 'draw_subtitle.raw']
    NOT_ADS = ['IMG_20231220_142355.jpg', '20190630_090136.mp4', '28439.jpg', 'DSC_0001.JPG',
               'IMG_1234.HEIC', 'P1000123.RAW', 'Screenshot_20230101-120000.png', 'icon_set.png',
               '20231220_142355.bmp', 'PXL_20231220_142355123.jpg', 'WP_20131115_002.mp4',
               # Numbered BMPs are the user's own pictures as often as ads
               '28439_2023-03-13.bmp', '8824_1269.bmp', 'imagebmp_10615.bmp', 'imagebmp (5).bmp']

    def test_names(self):
        for name in self.ADS:
            self.assertTrue(organize.is_ad_name(name), name)
        for name in self.NOT_ADS:
            self.assertFalse(organize.is_ad_name(name), name)

    def test_quarantine_moves_game_ads_but_keeps_a_camera_raw(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix='media-date-organizer-'))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        day = root / '2023-02-26'
        make_image(day / '492887-1648448524975-3d62u_2023-02-26.webp', fmt='WEBP')
        make_image(day / 'lbay6fy2_fftxeca_itehyhqsmpyyszx7_2023-03-03.gif', fmt='GIF')
        make_image(day / '8824_1269.bmp', fmt='BMP')
        (day / 'draw_title.raw').write_bytes(b'\0\0\x10\x20' * 64)
        # A camera RAW that happens to share the name pattern is kept
        (day / 'draw_camera.raw').write_bytes(b'IIU\x00' + b'\0' * 60)
        make_image(day / 'IMG_0001.jpg', taken=datetime.datetime(2023, 2, 26, 9, 0, 0))
        code, out = run(root, '--quarantine-ads', '--apply')
        self.assertEqual(code, 0, out)
        self.assertEqual(names(day), ['8824_1269.bmp', 'draw_camera.raw', 'img_0001.jpg'])
        self.assertEqual(len(names(root / '_ads' / '2023-02-26')), 3)
        self.assertIn('KEPT (camera: camera RAW header)', out)


if __name__ == '__main__':
    unittest.main()
